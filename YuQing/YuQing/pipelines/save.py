from YuQing.items import NewsItem


class MongoDBPipeline(object):

    def __init__(self, mongo_db, collection):
        self.mongo_db = mongo_db
        self.collection = collection

    @classmethod
    def from_settings(cls, settings):
        o = cls(
            mongo_db=settings.get('DB_MONGO'),
            collection=settings.get("COLLECTION_NEWS")
        )
        return o

    def process_item(self, item, spider):
        if isinstance(item, NewsItem):
            self.save_db(item)

    def save_db(self, item):
        self.mongo_db[self.collection].update_one({'newsUrl': item['newsUrl']}, {'$set': item}, upsert=True)
        print("save one>>>")
