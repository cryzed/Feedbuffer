import time
import zlib

from playhouse.fields import PickledField
import peewee

from feedbuffer import constants, log

database = peewee.SqliteDatabase(constants.DATABASE_PATH, threadlocals=True)
logger = log.get_logger(__name__)


class Model(peewee.Model):
    class Meta:
        database = database


# TODO: Use CompressedField and PickledField MI subclass
class CompressedPickledField(PickledField):
    def db_value(self, value):
        if value is not None:
            pickled = super().db_value(value)
            value = zlib.compress(pickled, zlib.Z_BEST_COMPRESSION)
            return value

    def python_value(self, value):
        if value is not None:
            decompressed = zlib.decompress(value)
            return super().python_value(decompressed)


class Feed(Model):
    url = peewee.TextField(unique=True)
    update_interval = peewee.IntegerField(default=constants.DEFAULT_UPDATE_INTERVAL)
    last_updated = peewee.IntegerField(default=0)
    data = CompressedPickledField()


class FeedItem(Model):
    id_ = peewee.TextField(unique=True)
    data = CompressedPickledField()
    feed = peewee.ForeignKeyField(Feed, related_name='entries')


database.create_tables([Feed, FeedItem], safe=True)


def _get_feed_query(url):
    return Feed.select().where(Feed.url == url)


def _feed_item_exists(feed, url):
    return FeedItem.select().where(FeedItem.feed == feed and FeedItem.id_ == url).exists()


def add_feed(url, feed_data):
    feed = Feed(url=url, data=feed_data.feed)
    feed.save()
    update_feed(feed_data)


def update_feed(feed_data):
    feed = get_feed(feed_data.href)
    data_source = tuple(
        {'id_': entry.id, 'data': entry, 'feed': feed} for entry in feed_data.entries
        if not _feed_item_exists(feed, entry.id)
    )

    logger.info('Updating feed: %s with %d new entries', feed_data.href, len(data_source))

    with database.atomic():
        FeedItem.insert_many(data_source).execute()
        feed.data = feed_data.feed
        feed.last_updated = time.time()
        feed.save()


def flush_feed(feed):
    query = FeedItem.delete().where(FeedItem.feed == feed)
    query.execute()


def feed_exists(url):
    return _get_feed_query(url).exists()


def get_feed(url):
    return _get_feed_query(url).get()
