# -*- coding: utf-8 -*-
import csv
from datetime import datetime
import re
from scrapy import signals
import json
import logging
import scrapy
from YuQing.items import NewsItem
from YuQing.loaders.loader import NewsItemLoader
from YuQing.utils.parse_plan import ParsePlan


class NewsSpider(scrapy.Spider):
    name = 'news'
    allowed_domains = ['sogou.com']
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page=1'  # sort 排序方式
    item = 0

    def __init__(self, **kwargs):
        self.start_time = datetime.now()
        self.news_comments_dict = dict()

    def spider_opened(self):
        logging.info("<------{} spider starting ------>".format(self.start_time))

    def spider_closed(self):
        # print("抓到{}个新闻".format(self.item))
        pass

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        if kwargs.get("_job"):
            kwargs.pop('_job')
        cls.from_settings(crawler.settings)
        spider = super(NewsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        cls.allowed_domains.extend(settings.get('ALLOWED_DOMAINS'))
        cls.mongo_db = settings.get("DB_MONGO")
        cls.col = settings.get("DB_PLAN")
        cls.spider_web_map = settings.get("SPIDERNAME_WEB_MAP")
        cls.project = settings.get("PLAN_PROJECT_SHOW")

    def start_requests(self):
        plans = self.mongo_db[self.col].find({}, projection=self.project)
        for plan in plans:
            logging.info("plan【{}】".format(plan))
            query_word_list = ParsePlan(plan).run()
            for query_word in query_word_list:
                logging.info("query_word【{}】".format(query_word))
                with open(self.news_file, "rU") as f:
                    reader = csv.DictReader(f)
                    for line in reader:
                        new_domains_uri = line.pop('new_domains_uri')
                        self.allowed_domains.append(new_domains_uri)
                        url = self.sogou_url_temp.format(new_domains_uri, query_word)
                        yield scrapy.Request(url, callback=self.parse, meta={'fields': line})

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, meta={'fields': response.meta["fields"]})

        next_url = response.xpath("//a[@id='sogou_next']/@href").extract_first()
        if next_url:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(next_url, callback=self.parse, meta={'fields': response.meta["fields"]})

    def parse_news(self, response):
        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        for name, xpath in response.meta['fields'].items():
            if xpath.startswith('re:'):
                item_loader.add_value(name, re.findall(xpath[3:], response.body.decode(response.encoding)))
            if xpath.startswith("/"):
                item_loader.add_xpath(name, xpath)
            if xpath.startswith("url"):
                item_loader.add_value(name, response.request.url)

        item = item_loader.load_item()

        # print(item)
        self.item += 1
        # yield item
