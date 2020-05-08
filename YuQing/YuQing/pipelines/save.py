from datetime import datetime

from YuQing.items import NewsItem


class MongoDBPipeline(object):

    def __init__(self, mongo_db, collection):
        self.mongo_db = mongo_db
        self.collection = "{0}_{1}".format(datetime.strftime(datetime.today(), "%Y%m"), collection)

    @classmethod
    def from_settings(cls, settings):
        o = cls(
            mongo_db=settings.get('DB_MONGO'),
            collection=settings.get("COLLECTION_NEWS")
        )
        return o

    def process_item(self, item, spider):
        if isinstance(item, NewsItem):
            item["createTime"] = datetime.now()
            item["updateTime"] = datetime.now()
            item["crawlerNumber"] = 1
            item["sensitive"] = 0  # 统一设置不敏感
            self.save_db(item)

    def save_db(self, item):
        self.mongo_db[self.collection].update_one({'newsUrl': item['newsUrl']}, {'$set': item}, upsert=True)
        print("save one>>>")
