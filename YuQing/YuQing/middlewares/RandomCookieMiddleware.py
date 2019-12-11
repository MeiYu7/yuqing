import pymongo
import requests
import logging
import json


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
            cookies = self.mongo_db[self.collection].find({}, projection=projectionFields).sort(
                [('_id', pymongo.ASCENDING)]).limit(1)

            for cookie in cookies:
                request.cookies = cookie

            return None


class SogouRandomCookieMiddleWare(object):
    def __init__(self, cookies_pool_url):
        self.logging = logging.getLogger("WeiBoMiddleWare")
        self.cookies_pool_url = cookies_pool_url

    @classmethod
    def from_settings(cls, settings):
        o = cls(cookies_pool_url=settings['SOGOU_COOKIES_URL'])
        return o

    def process_request(self, request, spider):
        if "sogou" in request.url:
            request.cookies = self.get_random_cookies()
            return None

    def get_random_cookies(self):

        try:
            response = requests.get(self.cookies_pool_url)
        except Exception as e:
            self.logging.info('Get Cookies failed: {}'.format(e))
        else:
            # 在中间件中，设置请求头携带的Cookies值，必须是一个字典，不能直接设置字符串。
            cookies = json.loads(response.text)
            self.logging.info('Get Cookies success: {}'.format(response.text))
            return cookies
