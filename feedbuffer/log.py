import logging

import cherrypy

from feedbuffer import settings

cherrypy.log.screen = False
cherrypy.log.error_log.propagate = False
cherrypy.log.access_log.propagate = False

_logger = logging.getLogger(__package__)
_logger.setLevel(settings.LOGGING_LEVEL)
_formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s')

# TODO: Use a configuration file instead
for handler in settings.LOGGING_HANDLERS:
    handler.setFormatter(_formatter)
    _logger.addHandler(handler)


def get_logger(name):
    package_prefix = __package__ + '.'
    if name.startswith(package_prefix):
        name = name[len(package_prefix):]

    return _logger.getChild(name)
