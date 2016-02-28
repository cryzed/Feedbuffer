import os

LOG_PATH = __package__ + '.log'
DATABASE_PATH = __package__ + '.db'
DEFAULT_UPDATE_INTERVAL = 180
MAXIMUM_UPDATE_WORKERS = (os.cpu_count() or 1) * 5
PORT = 8083
