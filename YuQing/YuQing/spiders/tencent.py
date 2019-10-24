# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from scrapy import signals
import re
from YuQing.items import NewsItem
from YuQing.loaders.loader import NewsItemLoader

class TencentSpider(scrapy.Spider):
    name = 'tencent'
    allowed_domains = ['sogou.com','qq.com']
    # start_urls = ['http://qq.com/']
    sogou_url_temp = 'https://news.sogou.com/news?query={}&sort=1&page={}'  # sort 排序方式
    # souhu_read_url = 'http://v2.sohu.com/public-api/articles/{}/pv'
    item = 0

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        print("抓到{}个新闻".format(self.item))


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(TencentSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        # cls.mongo_db = settings.get("DB_MONGO")
        # cls.cate_brand = settings.get("CATE_COLLECTION")
        pass

    def start_requests(self):
        query_word = 'site:qq.com 扶沟县'
        page = 1
        url = self.sogou_url_temp.format(query_word,page)
        print(url)
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news)


        next_url = response.xpath("//a[@id='sogou_next']/@href").extract_first()
        if next_url:
            next_url = response.urljoin(next_url)
            print('=====>',next_url)
            yield scrapy.Request(next_url,callback=self.parse)

    def parse_news(self, response):
        new_id = response.request.url.split('/')[-1].split('_')[0]

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        # item_loader.add_xpath("news_ori_title", "//article/p[@data-role='original-title']/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time", "//span[@class='a_time']/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department", "//span[@class='a_source']//text()")
        item_loader.add_xpath("news_reporter","//span[@class='a_author']/text()")
        item_loader.add_xpath("news_content", "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_xpath("news_content", "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_value("news_editor", re.findall(r"editor:'(.*?)'", response.body.decode(response.encoding)))
        item_loader.add_value("news_keyword", re.findall(r"tags:(\[.*?\]),", response.body.decode(response.encoding)))

        item = item_loader.load_item()
        self.item +=1
        print("===>",item)
        yield item