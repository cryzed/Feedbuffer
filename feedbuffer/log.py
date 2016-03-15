import logging

import cherrypy

from feedbuffer import settings

_PACKAGE_PREFIX = __package__ + '.'

_logger = logging.getLogger(__package__)
_logger.setLevel(settings.LOGGING_LEVEL)
_formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s')

cherrypy.log.screen = False
cherrypy.log.error_log.propagate = False
cherrypy.log.access_log.propagate = False

for handler in settings.LOGGING_HANDLERS:
    handler.setFormatter(_formatter)
    _logger.addHandler(handler)


def get_logger(name):
    if name.startswith(_PACKAGE_PREFIX):
        name = name[len(_PACKAGE_PREFIX):]

    return _logger.getChild(name)
