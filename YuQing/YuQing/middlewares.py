# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import time
import traceback
import datetime
from scrapy import signals
# from fake_useragent import UserAgent
from faker import Faker
from selenium.common.exceptions import TimeoutException
from scrapy.http import HtmlResponse
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
# from scrapy.conf import settings
from YuQing.items import ErrorItem,StatsItem
# from scrapy.log import logger


class YuqingSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class YuqingDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# 随机使用user_agent
class JdDownloadmiddlewareRandomUseragent(object):
    def __init__(self):
        # self.ua = UserAgent()
        self.f = Faker(locale='zh-CN')
    def process_request(self,request,spider):
        # useragent = self.ua.random
        useragent = self.f.user_agent()
        # print(useragent)
        request.headers.setdefault('User-Agent',useragent)


# 下载中间件，使用用selenium 爬取
class SeleniumMiddleware(object):
    def process_request(self, request, spider):
        """处理一切请求的方法"""

        # 这个if条件很重要，用来区分哪个请求使用selenium
        if request.meta.get("middleware") == "SeleniumMiddleware":
            try:
                # url是request自带的属性，可以直接调用请求
                spider.browser.get(request.url)
                # 这个方法是使窗口下拉
                spider.browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            except TimeoutException as e:
                print('超时')
                # 如果请求超时，就停止
                spider.browser.execute_script('window.stop()')
            # 休息2s，使页面加载完全
            time.sleep(2)
            # 返回加载后的页面response
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding="utf-8", request=request)


# 异常捕获中间件
class ProcessAllExceptionMiddleware(object):
    EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        self.mongo_db = settings.get('DB_MONGO')
        self.error = self.mongo_db[settings.get('MONGODB_ERROR', ErrorItem.collection)]

    @classmethod
    def from_settings(cls, settings):
        o = cls(settings)
        return o

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS):
            item = self.fill_item(request, exception, spider)
            self.save_db(item)
        return None

    def fill_item(self, request, exception, spider):
        item = ErrorItem()
        item['url'] = request.url
        item['title'] = spider.name
        item['type'] = type(exception).__name__
        item['content'] = traceback.format_exc()
        item['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return item

    def save_db(self, item):
        item = dict(item)
        self.error.update_one({'url': item['url'], 'type': item['type']}, {'$set': item}, upsert=True)


class StatCollectorMiddleware(object):
    def __init__(self, settings):
        self.mongo_db = settings.get('DB_MONGO')
        self.stat = self.mongo_db[settings.get('STATS_COLLECTION', StatsItem.collection)]

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_closed(self, spider):
        item = self.fill_item(spider)
        self.save_db(item)

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

    def save_db(self,item):
        item = dict(item)
        self.stat.insert_one(item)


# 处理sogou验证码
class AntispiderRequestMiddlewere(object):

    # def __init__(self):
    #     self.ua = UserAgent()

    def process_request(self,request,spider):

       if "antispider" in request.url:

           print("Sogou正在进行验证码验证")

