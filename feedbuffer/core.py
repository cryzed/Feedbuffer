import concurrent.futures
import sched

import bs4
import cachecontrol
import feedparser
import requests
import requests.exceptions

from feedbuffer import constants, database, log

executor = concurrent.futures.ThreadPoolExecutor(max_workers=constants.MAXIMUM_UPDATE_WORKERS)
logger = log.get_logger(__name__)
scheduled = {}
scheduler = sched.scheduler()
session = cachecontrol.CacheControl(requests.Session())
session.headers['User-Agent'] = constants.USER_AGENT


def get_feed_entries(soup):
    return [item for item in soup(['item', 'entry'])]


def update_feed(url):
    try:
        response = session.get(url, timeout=constants.REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        return

    soup = bs4.BeautifulSoup(response.text, 'xml')
    entries = get_feed_entries(soup)
    feed = feedparser.parse(response.text)

    entry_ids = [entry.id for entry in feed.entries]
    database.update_feed(url, response.text, zip(entry_ids, (str(entry) for entry in entries)))


def update_and_reschedule_feed(url):
    executor.submit(update_feed, url)
    schedule_feed_update(url)


def schedule_feed_update(url):
    if url in scheduled:
        if scheduled[url] in scheduler.queue:
            try:
                scheduler.cancel(scheduled[url])
            except ValueError:
                pass
        del scheduled[url]

    if not database.feed_exists(url):
        return

    feed = database.get_feed(url)
    event = scheduler.enter(feed.update_interval, 1, update_and_reschedule_feed, (url,))
    scheduled[url] = event


def delete_feed_entries(soup):
    for entry in get_feed_entries(soup):
        entry.decompose()


def generate_feed(feed_data, entries):
    feed = bs4.BeautifulSoup(feed_data, 'xml')
    delete_feed_entries(feed)
    root = feed.find(['rss', 'feed'])
    for entry in entries:
        entry = bs4.BeautifulSoup(entry, 'xml')
        entry = entry.find(['item', 'entry'])
        root.insert(0, entry)

    return str(feed).encode(constants.ENCODING)
