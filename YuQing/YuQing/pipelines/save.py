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
            print("save one   ")

    def save_db(self, item):
        self.mongo_db[self.collection].update_one({'news_url': item['news_url']}, {'$set': item}, upsert=True)
