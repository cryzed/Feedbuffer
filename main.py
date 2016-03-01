import threading
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
    threading.Thread(target=lambda: cherrypy.quickstart(Server())).start()
    while True:
        core.scheduler.run()
        time.sleep(1)


if __name__ == '__main__':
    main()
