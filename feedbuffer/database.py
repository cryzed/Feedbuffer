import peewee

from feedbuffer import constants, log

database = peewee.SqliteDatabase(constants.DATABASE_PATH)
logger = log.get_logger(__name__)


class Model(peewee.Model):
    class Meta:
        database = database


class Feed(Model):
    url = peewee.TextField(unique=True)
    update_interval = peewee.IntegerField(default=constants.DEFAULT_UPDATE_INTERVAL)

    # Storing an already decoded version of the feed would be possible, but that would mean converting the BeautifulSoup
    # into an unicode string which seems to change the feed contents in subtle ways quite often -- preventing it from
    # being parsed back into a valid BeautifulSoup instance.
    data = peewee.BlobField()
    encoding = peewee.TextField()


class FeedItem(Model):
    id_ = peewee.TextField(unique=True)
    data = peewee.TextField()
    feed = peewee.ForeignKeyField(Feed, related_name='entries')


database.create_tables([Feed, FeedItem], safe=True)


def _get_feed_query(url):
    return Feed.select().where(Feed.url == url)


def _feed_item_exists(feed, id_):
    return FeedItem.select().where(FeedItem.feed == feed and FeedItem.id_ == id_).exists()


def feed_exists(url):
    return _get_feed_query(url).exists()


def get_feed(url):
    return _get_feed_query(url).get()


def update_feed(url, feed_data, entries, encoding):
    if feed_exists(url):
        feed = get_feed(url)
    else:
        feed = Feed(url=url, data=feed_data, encoding=encoding)
        feed.save()

    data_source = tuple(
        {'id_': id_, 'data': entry, 'feed': feed} for (id_, entry) in entries
        if not _feed_item_exists(feed, id_)
    )

    logger.info('Updating feed: %s with %d new entries...', url, len(data_source))

    with database.atomic():
        FeedItem.insert_many(data_source).execute()
        feed.data = feed_data
        feed.save()


def flush_feed(feed):
    query = FeedItem.delete().where(FeedItem.feed == feed)
    query.execute()
