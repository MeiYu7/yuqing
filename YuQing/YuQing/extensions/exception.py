import datetime

from scrapy import signals

from YuQing.items import ErrorItem, NewsItem


class SpiderExceptionExtension(object):

    def __init__(self, mongo_db, error):
        self.db = mongo_db
        self.error_collection = mongo_db[error]

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(mongo_db=crawler.settings.get('DB_MONGO'),
                  error=crawler.settings.get('MONGODB_ERROR', ErrorItem.collection)
                  )
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext

    def spider_error(self, failure, response, spider):
        error_item = ErrorItem()
        error_item['url'] = response.url
        error_item['title'] = spider.name
        error_item['type'] = repr(failure)
        error_item['content'] = failure.getTraceback()
        error_item['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        self.insert_db(error_item)

    def insert_db(self, error_item):
        item = dict(error_item)
        self.error_collection.update_one({'url': item['url'], 'type': item['type']}, {'$set': item}, upsert=True)


class FieldErrorExtension(object):

    def __init__(self, mongo_db, error):
        self.mongo_db = mongo_db
        self.error = error

    @classmethod
    def from_crawler(cls, crawler):
        mongo_db = crawler.settings.get('DB_MONGO')
        ext = cls(mongo_db, NewsItem.collection_exception)
        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        return ext

    def item_dropped(self, item, exception, spider):
        try:
            item['error'] = eval(str(exception))
        except Exception as e:
            item['error'] = str(exception)
        self.insert_db(item)

    def insert_db(self, item):
        item = dict(item)
        self.mongo_db[self.error].update_one({'error': item['error'], 'news_url': item['news_url']}, {'$set': item}, upsert=True)
