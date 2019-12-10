"""
数据收集中间件
"""
from scrapy import signals

from YuQing.items import StatsItem


class StatCollectorMiddleware(object):
    def __init__(self, settings):
        self.mongo_db = settings.get('DB_MONGO')
        self.stat = self.mongo_db[settings.get('STATS_COLLECTION', StatsItem.collection)]
        self.browser = settings.get('seleniumBrowser')

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_closed(self, spider):
        item = self.fill_item(spider)
        self.save_db(item)
        if self.browser:
            self.browser.close()

    def fill_item(self, spider):
        stats = spider.crawler.stats.get_stats()
        item = StatsItem()
        item['startTime'] = stats.get("startTime")
        item['finishTime'] = stats.get("finishTime")
        item['finishReason'] = stats.get("finishReason")
        item['itemScrapedCount'] = stats.get("itemScrapedCount")
        item['responseReceivedCount'] = stats.get("responseReceivedCount")
        item['itemDroppedCount'] = stats.get("itemDroppedCount")
        item['responseReceivedCount'] = stats.get("responseReceivedCount")
        item["finalFindIds"] = stats.get("finalFindIds")
        item["finalFindIds"] = stats.get("finalFindIds")
        # item["time_secodes_consum"] = stats.get("time_secodes_consum")
        return item

    def save_db(self, item):
        item = dict(item)
        self.stat.insert_one(item)
