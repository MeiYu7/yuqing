# -*- coding: utf-8 -*-
import csv
from datetime import datetime
import re
from scrapy import signals
import json
import scrapy
from YuQing.items import NewsItem
from YuQing.loaders.loader import NewsItemLoader


class NewsSpider(scrapy.Spider):
    name = 'news'
    allowed_domains = ['sogou.com']
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page=1'  # sort 排序方式
    item = 0

    # def __init__(self):
    #     self.reader = ""

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()
        # f =  open(self.news_file, "rU")
        # self.reader = csv.DictReader(f)
        # f.close()

    def spider_closed(self):
        print("抓到{}个新闻".format(self.item))

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
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
        cls.news_file = settings.get("NEWS_FILE")
        # cls.key_word = settings.get("TEST_KEYWORD")

    def start_requests(self):
        plans = self.mongo_db[self.col].find()
        for plan in plans:
            # print(plan)
            query_word = plan["areas"] + " " + plan["plan_name"] + " " + plan["events"]
            print(query_word)
            # query_word = self.key_word
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
        yield item
