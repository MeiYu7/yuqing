import re
import pymongo
import redis


class RedisDB(object):

    def __init__(self, crawler):
        redis_url = crawler.settings.get('REDIS_URL')
        if redis_url:
            re_result = re.match(r'redis://:(.*?)@(.*?):(\d+)', redis_url)
            if re_result:
                self.password = re_result.group(1)
                self.host = re_result.group(2)
                self.port = re_result.group(3)
        else:
            self.password = crawler.settings.get('REDIS_PASSWORD')
            self.host = crawler.settings.get('REDIS_HOST')
            self.port = crawler.settings.get('REDIS_PORT')

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler)
        o.set_redis(crawler.settings)
        return o

    def set_redis(self, settings):
        redis_db = redis.Redis(host=self.host, port=self.port, password=self.password, decode_responses=True)
        settings.set('DB_REDIS', redis_db)


class MonGoDB(object):
    def __init__(self, settings):
        self.mongo_uri = settings.get('MONGO_URI', 'mongodb://localhost:27017')
        self.mongo_db_name = settings.get('MONGO_DATABASE', 'jd')

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        o = cls(settings)
        o.set_mongo(settings)
        return o

    def set_mongo(self, settings):
        mongo_client = pymongo.MongoClient(self.mongo_uri)
        mongo_db = mongo_client[self.mongo_db_name]

        settings.set('CLIENT_MONGO', mongo_client)
        settings.set('DB_MONGO', mongo_db)