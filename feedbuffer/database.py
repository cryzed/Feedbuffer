import concurrent.futures
import functools

import peewee

from feedbuffer import settings, log

_database = peewee.SqliteDatabase(settings.DATABASE_PATH)
_logger = log.get_logger(__name__)

# Easy way to queue function calls and execute them in a single thread, without having to manually write
# producer-consumer logic.
_database_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


class Model(peewee.Model):
    class Meta:
        database = _database


class Feed(Model):
    url = peewee.TextField(unique=True)
    update_interval = peewee.IntegerField(default=settings.DEFAULT_UPDATE_INTERVAL)
    data = peewee.TextField()


class FeedItem(Model):
    id_ = peewee.TextField(unique=True)
    data = peewee.TextField()
    feed = peewee.ForeignKeyField(Feed, related_name='entries')


_database.create_tables([Feed, FeedItem], safe=True)


def _execute_in(executor):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            future = executor.submit(function, *args, **kwargs)
            return future.result()

        return wrapper

    return decorator


def _get_feed_query(url):
    return Feed.select().where(Feed.url == url)


def _feed_item_exists(feed, id_):
    return FeedItem.select().where(FeedItem.feed == feed and FeedItem.id_ == id_).exists()


def _feed_exists(url):
    return _get_feed_query(url).exists()


def _get_feed(url):
    return _get_feed_query(url).get()


@_execute_in(_database_executor)
def feed_exists(url):
    return _get_feed_query(url).exists()


@_execute_in(_database_executor)
def get_feed(url):
    return _get_feed(url)


@_execute_in(_database_executor)
def update_feed(url, feed_data, entries):
    if _feed_exists(url):
        feed = _get_feed(url)
    else:
        feed = Feed(url=url, data=feed_data)
        feed.save()

    data_source = [
        {'id_': id_, 'data': entry, 'feed': feed} for (id_, entry) in entries if not _feed_item_exists(feed, id_)
    ]

    _logger.info('Updating feed: %s with %d new entries...', url, len(data_source))

    with _database.atomic():
        FeedItem.insert_many(data_source).execute()
        feed.data = feed_data
        feed.save()


@_execute_in(_database_executor)
def flush_feed(feed):
    query = FeedItem.delete().where(FeedItem.feed == feed)
    query.execute()


# Generic way to update data in a model instance using the write executor
@_execute_in(_database_executor)
def update_model_data(model, **kwargs):
    for key, value in kwargs.items():
        setattr(model, key, value)

    model.save()
