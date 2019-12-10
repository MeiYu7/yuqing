import datetime

from scrapy import signals


class CoreStats(object):

    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.stats)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(o.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(o.item_dropped, signal=signals.item_dropped)
        crawler.signals.connect(o.response_received, signal=signals.response_received)
        return o

    def spider_opened(self, spider):
        self.stats.set_value('startTime', datetime.datetime.now(), spider=spider)

    def spider_closed(self, spider, reason):
        self.stats.set_value('finishTime', datetime.datetime.now(), spider=spider)
        self.stats.set_value('finishReason', reason, spider=spider)

    def item_scraped(self, item, spider):
        self.stats.inc_value('itemScrapedCount', spider=spider)

    def response_received(self, spider):
        self.stats.inc_value('responseReceivedCount', spider=spider)

    def item_dropped(self, item, spider, exception):
        # reason = exception.__class__.__name__
        self.stats.inc_value('itemDroppedCount', spider=spider)
        # self.stats.inc_value('item_dropped_reasons_count/%s' % reason, spider=spider)