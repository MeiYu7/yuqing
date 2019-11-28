# -*- coding: utf-8 -*-
import json
import re

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class PeopleSpider(scrapy.Spider):
    name = 'people'
    allowed_domains = ['people.com.cn', "sogou.com"]
    start_urls = ['http://legal.people.com.cn/n1/2019/1127/c42510-31476018.html']

    start_uri = "people.com.cn"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式

    # comment_url_temp = "http://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/{news_id}/comments/newList?limit=30&showLevelThreshold=72&offset={page}"
    # fisrt_comment_temp = "http://comment.sina.com.cn/page/info?format=json&channel={0}&newsid={1}&ie=utf-8&oe=utf-8&page={2}&page_size=100"
    item = 0

    def __init__(self):
        self.news_comments_dict = dict()

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        # print("抓到{}个新闻".format(self.item))
        pass

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(PeopleSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        cls.allowed_domains.extend(settings.get('ALLOWED_DOMAINS'))
        cls.mongo_db = settings.get("DB_MONGO")
        cls.col = settings.get("DB_PLAN")

    def start_requests(self):
        plans = self.mongo_db[self.col].find()
        for plan in plans:
            # print(plan)
            # query_word = plan["areas"] + plan["events"]
            # print(query_word)
            query_word = '杀人'
            url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
            print(url)
            yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={"query_word": query_word})

    def parse(self, response):
        print("parse==>", response.request.url)
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True)

        next_url = response.xpath("//a[@id='sogou_next']/@href").extract_first()
        if next_url is not None:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)

    def parse_news(self, response):
        """解析新闻"""
        print("parse_news==>", response.request.url)

        news_id = response.request.url.split("-")[-1].split(".")[0]
        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//div[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time", "//div[@class='box01']/div[@class='fl']/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department", "//div[@class='box01']/div[@class='fl']/a/text()")
        item_loader.add_xpath("news_reporter", "//p[@class='author']/text()")
        item_loader.add_xpath("news_content", "//div[@class='box_con']//p/text()")
        item_loader.add_xpath("news_editor", "//div[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_value("news_keyword", "")
        item_loader.add_value("news_comments", [])
        item = item_loader.load_item()


        # read_num
        comment_url = response.xpath("//div[@class='message']/a/@href").extract_first()
        if comment_url is not None:
            yield scrapy.Request(comment_url, callback=self.parse_read_num, meta={"item": item}, dont_filter=True)
        else:
            # yield item
            pass

    def parse_read_num(self, response):
        print("parse_read_num===>", response.request.url)

        news_comments_num = response.xpath("//span[@class='replayNum']/text()").extract_first()
        print(news_comments_num)
        total_page_no = news_comments_num // 100 + 1
        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item, response=response)
        item_loader.add_xpath("news_read_num", "//span[@class='readNum']/text()")
        item_loader.add_xpath("news_comments_num", "//span[@class='replayNum']/text()")
        item_loader.add_xpath("news_comments_num", "//span[@class='replayNum']/text()")
        item = item_loader.load_item()
        print(item)
        print("**********************************************")

        # comments
        if int(news_comments_num) > 0:
            li_list = response.xpath("//ul[@class='subUL']/li")

            for li in li_list:
                # 单条评论
                comment_loader = NewsCommentsItemLoader(item=CommentsItem(), selector=li)

                comment_loader.add_xpath("reviewers_nickname", "./p/a[@class='userNick']/text()")
                comment_loader.add_xpath("content", "./p/a[@class='treeReply']/text()")
                comment_dict = comment_loader.load_item()
                print(comment_dict)


