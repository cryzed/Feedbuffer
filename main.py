import threading
import traceback
import time

import cherrypy

from feedbuffer import core, log
from feedbuffer.constants import PORT
from feedbuffer.server import Server

logger = log.get_logger(__name__)


def main():
    cherrypy.config.update({'server.socket_port': PORT, 'server.socket_host': '0.0.0.0'})
    cherrypy.config['server.socket_port'] = PORT
    cherrypy.config['checker.check_skipped_app_config'] = False

    logger.info('Starting CherryPy server...')
    threading.Thread(target=cherrypy.quickstart, args=(Server(),)).start()

    logger.info('Starting scheduler loop...')
    while True:
        try:
            core.scheduler.run()
        except Exception:
            logger.warn(traceback.format_exc())
        time.sleep(1)


if __name__ == '__main__':
    main()
