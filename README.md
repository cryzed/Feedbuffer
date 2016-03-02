# Feedbuffer
Feedbuffer buffers RSS and Atom syndication feeds, that is to say it caches new feed entries until the news aggregator requests them and then generates the syndication feed with all cached entries.

This is will be mostly useful to people who read feeds with a very high throughput, only use their news aggregator very rarely or simply want to make very sure that they aren't missing any entries.


## Usage
Install the requirements: `pip install peewee feedparser requests cachecontrol lxml beautifulsoup4 cherrypy` and run `main.py`. By default a HTTP server will respond on http://0.0.0.0:8083/ (check constants.py for more configuration options). Instead of requesting the target feed directly in your news aggregator, prefix the URL like this: `http://0.0.0.0:8083/?url=<url>` where `url` is a URL-quoted version of the original feed URL:

```
>>> from urllib.parse import quote_plus
>>> quote_plus('https://www.reddit.com/.rss')
'https%3A%2F%2Fwww.reddit.com%2F.rss'
>>>
```

Additionally `&update_interval=<integer>` can be used to adjust the interval in which Feedbuffer will check for updates to the feed (default is 180 seconds).


## Details
Feedbuffer will attempt to fix invalid feed entries with a missing unique identifier field by generating the SHA-1 sum of the entry's content and inserting it. The log file will be generated as `feedbuffer.log` in the current working directory.
