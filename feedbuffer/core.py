from datetime import datetime
import concurrent.futures
import sched

from django.utils import feedgenerator
import feedparser

from feedbuffer import constants, database, log

ENCODING = 'UTF-8'

executor = concurrent.futures.ThreadPoolExecutor(max_workers=constants.MAXIMUM_UPDATE_WORKERS)
logger = log.get_logger(__name__)
scheduled = {}
scheduler = sched.scheduler()


def add_feed(url):
    feed_data = feedparser.parse(url)
    database.add_feed(feed_data)


def update_feed(url):
    feed_data = feedparser.parse(url)
    database.update_feed(feed_data)


def update_and_reschedule_feed(url):
    executor.submit(update_feed, url)
    schedule_feed_update(url)


def schedule_feed_update(url):
    if url in scheduled:
        if scheduled[url] in scheduler.queue:
            logger.debug('URL was already scheduled, cancelling: %s', url)
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
    author_detail = feed_data.get('author_detail', {})
    feed_generator = feedgenerator.Atom1Feed(
        feed_data.title,
        feed_data.link,
        feed_data.get('description', ''),
        feed_data.get('language', None),
        author_detail.get('email', None),
        author_detail.get('name', None),
        author_detail.get('href', None),
        feed_data.get('subtitle', None),
        [tag.term for tag in feed_data.get('tags', [])] or None,
        feed_data.get('href', None),
        feed_data.get('rights', None),
        feed_data.get('id_', None),
        feed_data.get('ttl', None),
    )

    for entry in entries:
        author_detail = entry.get('author_detail', {})
        feed_generator.add_item(
            entry.title,
            entry.link,
            entry.get('description', ''),
            author_detail.get('email', None),
            author_detail.get('name', None),
            author_detail.get('href', None),
            datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None,
            entry.get('comments', None),
            entry.get('id_', None),
            None,
            None,
            [tag.term for tag in entry.get('tags', [])] or None,
            entry.get('rights', None),
            entry.get('ttl', None),
            datetime(*entry.updated_parsed[:6]) if 'updated_parsed' in entry else None
        )

    return feed_generator.writeString(ENCODING)
