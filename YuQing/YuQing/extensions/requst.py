from scrapy import signals


class BeforeFilterRequest(object):
    """修改爬虫的request对象的dont_filter属性"""

    def __init__(self, crawler):
        self.dont_filter = crawler.settings.getbool('DONT_FILTER_REQUEST')

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler)
        crawler.signals.connect(o.request_scheduled, signal=signals.request_scheduled)
        return o

    def request_scheduled(self, request, spider):
        if self.dont_filter:
            request.dont_filter = self.dont_filter



# from scrapy_redis_bloomfilter.defaults import BLOOMFILTER_HASH_NUMBER, BLOOMFILTER_BIT, DUPEFILTER_DEBUG, DUPEFILTER_KEY
# from scrapy_redis_bloomfilter.bloomfilter import BloomFilter


# class NextExtension(object):
#     """这个扩展是基于布隆过滤器的"""
#
#     def __init__(self, server, key, debug, bit, hash_number):
#         self.bf = BloomFilter(server, key, bit, hash_number)
#
#     @classmethod
#     def from_settings(cls, settings):
#         key = DUPEFILTER_KEY % {'timestamp': int(time.time())}
#         debug = settings.getbool('DUPEFILTER_DEBUG', DUPEFILTER_DEBUG)
#         bit = settings.getint('BLOOMFILTER_BIT', BLOOMFILTER_BIT)
#         hash_number = settings.getint('BLOOMFILTER_HASH_NUMBER', BLOOMFILTER_HASH_NUMBER)
#         server = settings.get('DB_REDIS')
#         return cls(server, key=key, debug=debug, bit=bit, hash_number=hash_number)
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         instance = cls.from_settings(crawler.settings)
#         crawler.signals.connect(instance.is_next, signal=signals.request_scheduled)
#         return instance
#
#     def is_next(self, request, spider):
#         if not self.is_dont_filter(request):
#             next = self.exists(request)
#
#     def is_dont_filter(self, request):
#         return request.request.dont_filter
#
#     def exists(self, request):
#         fp = self.request_fingerprint(request)
#         if self.bf.exists(fp):
#             return True
#         return False
#
#     def request_fingerprint(self, request):
#         return request_fingerprint(request)