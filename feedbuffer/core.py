import concurrent.futures
import hashlib
import sched

import bs4
import cachecontrol
import feedparser
import requests
import requests.exceptions

from feedbuffer import constants, database, log

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=constants.MAXIMUM_UPDATE_WORKERS)
_logger = log.get_logger(__name__)
_session = cachecontrol.CacheControl(requests.Session())
_session.headers['User-Agent'] = constants.USER_AGENT
scheduled = {}
scheduler = sched.scheduler()

# XML-processing instructions have to end with "?>". The original code erroneously ends them with ">" which leads to
# errors in almost all parsers, including BeautifulSoup with the lxml treebuilder itself -- so we fix this at runtime.
bs4.element.ProcessingInstruction.SUFFIX = '?>'


def extract_feed_entries(soup):
    return [item.extract() for item in soup(['item', 'entry'])]


def update_feed(url):
    try:
        response = _session.get(url, timeout=constants.REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        return

    # Don't let requests do the content decoding, instead just supply the encoding detected by requests and let
    # BeautifulSoup and the treebuilder do their thing. For example: BeautifulSoup4 with the lxml treebuilder only
    # correctly parses content with <content:encoded> tags when it can decode the bytes by itself.
    try:
        soup = bs4.BeautifulSoup(response.content, 'xml', from_encoding=response.encoding)
    except UnicodeDecodeError:
        soup = bs4.BeautifulSoup(response.content, 'xml', from_encoding=response.apparent_encoding)

    entries = extract_feed_entries(soup)

    # TODO: Remove the feedparser dependency and figure out all ways to get access to the feed item id
    parsed_feed = feedparser.parse(response.text)

    entry_ids = []
    for index, parsed_entry in enumerate(parsed_feed.entries):
        id_ = parsed_entry.get('id', None)
        if id_ is None:
            id_ = hashlib.sha1(entries[index].encode(constants.ENCODING)).hexdigest()
            _logger.warn('No identifier found for entry %d of %s. Inserting SHA-1 id: %s...', index, url, id_)
            id_tag = soup.new_tag('guid' if parsed_feed.version.startswith('rss') else 'id')
            id_tag.string = id_
            entries[index].append(id_tag)
        entry_ids.append(id_)

    database.update_feed(url, str(soup), zip(entry_ids, (str(entry) for entry in entries)))


def update_and_reschedule_feed(url):
    _executor.submit(update_feed, url)
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


def generate_feed(feed_data, entries):
    feed = bs4.BeautifulSoup(feed_data, 'xml')
    root = feed.find(['rss', 'feed'])
    for entry in entries:
        entry = bs4.BeautifulSoup(entry, 'xml')
        entry = entry.find(['item', 'entry'])
        root.insert(len(root.contents), entry)

    return str(feed).encode(constants.ENCODING)
