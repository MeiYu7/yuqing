import pymongo


class RandomCookieMiddleware(object):

    def __init__(self, settings):
        self.mongo_db = settings.get('DB_MONGO')
        self.collection = settings.get("SOGOU_COOKIE_POOL_NAME", "sogou_cookie_pool")

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        return o

    def process_request(self, request, spider):
        if "sogou.com" in request.url:
            projectionFields = {'SNUID': True, 'SUID': True, 'SUV': True, '_id': False}
            cookies = self.mongo_db[self.collection].find({}, projection=projectionFields).sort([('_id', pymongo.ASCENDING)]).limit(1)

            for cookie in cookies:
                request.cookies = cookie

            return None
