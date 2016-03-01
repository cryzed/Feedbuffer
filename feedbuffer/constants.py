import os

DATABASE_PATH = __package__ + '.db'
DEFAULT_UPDATE_INTERVAL = 180
ENCODING = 'UTF-8'
LOG_PATH = __package__ + '.log'
MAXIMUM_UPDATE_WORKERS = (os.cpu_count() or 1) * 5
PORT = 8083
REQUEST_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0'
