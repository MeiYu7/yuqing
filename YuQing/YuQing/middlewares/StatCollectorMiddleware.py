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
        item['start_time'] = stats.get("start_time")
        item['finish_time'] = stats.get("finish_time")
        item['finish_reason'] = stats.get("finish_reason")
        item['item_scraped_count'] = stats.get("item_scraped_count")
        item['item_dropped_count'] = stats.get("item_dropped_count")
        # item['item_dropped_reasons_count'] = stats.get("item_dropped_reasons_count")
        item['response_received_count'] = stats.get("response_received_count")
        item["finaly_insert_item"] = stats.get("finaly_insert_item")
        item["finaly_find_ids"] = stats.get("finaly_find_ids")
        item["time_secodes_consum"] = stats.get("time_secodes_consum")
        return item

    def save_db(self, item):
        item = dict(item)
        self.stat.insert_one(item)
