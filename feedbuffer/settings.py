import logging
import os

DATABASE_PATH = __package__ + '.db'
DEFAULT_UPDATE_INTERVAL = 180
ENCODING = 'UTF-8'
LOGGING_HANDLERS = [logging.FileHandler(__package__ + '.log')]
LOGGING_LEVEL = logging.WARNING
MAXIMUM_UPDATE_WORKERS = (os.cpu_count() or 1) * 5
PORT = 8083
REQUEST_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'
