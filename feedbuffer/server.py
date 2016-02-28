import cherrypy

from feedbuffer import core, database, log
from feedbuffer.constants import DEFAULT_UPDATE_INTERVAL

logger = log.get_logger(__name__)


class Server:
    @cherrypy.expose
    def index(self, url, update_interval=DEFAULT_UPDATE_INTERVAL):
        if not database.feed_exists(url):
            logger.info('Adding new URL: %s', url)
            core.executor.submit(core.add_feed, url)
            core.schedule_feed_update(url)
            return
        elif url not in core.scheduled:
            logger.info('Updating existing URL: %s', url)
            core.executor.submit(core.update_feed, url)
            core.schedule_feed_update(url)

        feed = database.get_feed(url)
        update_interval = int(update_interval)
        if feed.update_interval != update_interval:
            logger.info('Changing update interval from %d to %d for feed: %s',
                        feed.update_interval, update_interval, url)
            feed.update_interval = update_interval
            feed.save()
            core.schedule_feed_update(url)

        logger.info('Generating feed: %s with %d entries...', url, len(feed.entries))
        response = core.generate_feed(feed.data, [entry.data for entry in feed.entries])
        database.flush_feed(feed)
        return response