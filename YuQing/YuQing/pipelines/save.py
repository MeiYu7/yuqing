import os
from datetime import datetime, timezone, timedelta

from YuQing.items import NewsItem


class MongoDBPipeline(object):

    def __init__(self, mongo_db, collection, checkFile):
        self.mongo_db = mongo_db
        self.collection = collection
        self.checkFile = checkFile

    @classmethod
    def from_settings(cls, settings):
        o = cls(
            mongo_db=settings.get('DB_MONGO'),
            collection=settings.get("COLLECTION_NEWS"),
            checkFile=settings.get("CHECK_FILE")
        )
        return o

    def close_spider(self, spider):
        if os.path.isfile(self.checkFile):
            os.remove(self.checkFile)

    def process_item(self, item, spider):
        if isinstance(item, NewsItem):
            item["createTime"] = datetime.utcnow().replace(tzinfo=timezone.utc)
            item["updateTime"] = datetime.utcnow().replace(tzinfo=timezone.utc)
            item["crawlerNumber"] = 1
            item["sensitive"] = 0  # 统一设置不敏感
            self.save_db(item)

    def get_collection_name(self):
        collection_month = "{}_{}".format(datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y%m"),
                                          self.collection)

        return collection_month

    def save_db(self, item):

        self.mongo_db[self.get_collection_name()].update_one({'newsUrl': item['newsUrl']}, {'$set': item}, upsert=True)
        print(datetime.now(), "save one>>>")
