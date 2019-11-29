import datetime
import traceback

from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
from YuQing.items import ErrorItem
# 异常捕获中间件


class ProcessAllExceptionMiddleware(object):
    EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                  ConnectionRefusedError, ConnectionDone, ConnectError,
                  ConnectionLost, TCPTimedOutError, ResponseFailed,
                  IOError, TunnelError)

    def __init__(self, settings):
        self.mongo_db = settings.get('DB_MONGO')
        self.error = self.mongo_db[settings.get('MONGODB_ERROR', ErrorItem.collection)]

    @classmethod
    def from_settings(cls, settings):
        o = cls(settings)
        return o

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS):
            item = self.fill_item(request, exception, spider)
            self.save_db(item)
        return None

    def fill_item(self, request, exception, spider):
        item = ErrorItem()
        item['url'] = request.url
        item['title'] = spider.name
        item['type'] = type(exception).__name__
        item['content'] = traceback.format_exc()
        item['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return item

    def save_db(self, item):
        item = dict(item)
        self.error.update_one({'url': item['url'], 'type': item['type']}, {'$set': item}, upsert=True)