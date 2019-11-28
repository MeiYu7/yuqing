# -*- coding: utf-8 -*-
import json
import re

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class IfengSpider(scrapy.Spider):
    name = 'ifeng'
    allowed_domains = ['ifeng.com', 'sogou.com']
    # start_urls = ['http://ifeng.com/']

    start_uri = "ifeng.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式

    comment_url_temp = "https://comment.ifeng.com/get.php?docUrl=ucms_{0}&job=1&p={1}&pageSize=20"
    # fisrt_comment_temp = "http://comment.sina.com.cn/page/info?format=json&channel={0}&newsid={1}&ie=utf-8&oe=utf-8&page={2}&page_size=100"
    item = 0

    def __init__(self):
        self.news_comments_list = list()

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        # print("抓到{}个新闻".format(self.item))
        pass

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(IfengSpider, cls).from_crawler(crawler, *args, **kwargs)
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
        """解析凤凰网新闻"""
        print("parse_news==>", response.request.url)
        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time",
                              "//div[contains(@class,'info') or contains(@class,'caption') or contains(@id,'artical')]/p/span/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department",
                              "//span[contains(@itemprop, 'publisher') or contains(@class, 'source')]//text()")
        item_loader.add_xpath("news_reporter", "//p[contains(text(), '记者')]/text()")
        item_loader.add_xpath("news_content",
                              "//div[contains(@id,'content') or contains(@id,'artical') or contains(@class, 'text')]//p/text()")
        item_loader.add_xpath("news_editor", "//p[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_value("news_keyword", "")
        item_loader.add_value("news_comments", [])
        item = item_loader.load_item()
        print(item)

        # comments
        news_id = response.request.url.split("/")[-1]

        comment_url = self.comment_url_temp.format(news_id, "1")
        yield scrapy.Request(comment_url, callback=self.parse_comment, meta={"item": item, "news_id": news_id})

    def parse_one_comment(self, comment_loader, comment):
        comment_loader.add_value("comment_id", comment["comment_id"])
        comment_loader.add_value("content", comment["comment_contents"])
        comment_loader.add_value("comment_time", comment["comment_date"])
        comment_loader.add_value("support_count", comment["uptimes"])
        comment_loader.add_value("against_count", "")
        comment_loader.add_value("reviewers_id", comment["user_id"])
        comment_loader.add_value("reviewers_addr", comment["ip_from"])
        comment_loader.add_value("reviewers_nickname", comment["uname"])
        comment_loader.add_value("parent_id", comment["quote_id"])
        comment_dict = comment_loader.load_item()

        return comment_dict

    def parse_comment(self, response):
        print("requesting...... comment==>", response.request.url)
        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)

        data = json.loads(response.body.decode(response.encoding))
        comment_num = data["count"]
        total_page_no = comment_num // 20 + 1

        if comment_num != 0 and len(data["comments"]) > 0:
            for comment in data["comments"]:
                comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                comment_dict = self.parse_one_comment(comment_loader, comment)
                self.news_comments_list.append(comment_dict)

                # 获取父级评论
                if len(comment["parent"]) >0:
                    for p_comment in comment["parent"]:
                        p_comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                        p_comment_dict = self.parse_one_comment(p_comment_loader, p_comment)
                        self.news_comments_list.append(p_comment_dict)

        # 获取下一页评论
        if total_page_no >= 2:
            for i in range(2, total_page_no + 1):
                next_comment_url = self.comment_url_temp.format(response.meta["news_id"], str(i))
                yield scrapy.Request(next_comment_url, callback=self.parse_comment,
                                     meta={"item": item, "news_id": response.meta["news_id"]})

        if len(self.news_comments_list) == comment_num:
            item_loader.add_value("news_comments_num", comment_num)
            item_loader.add_value("news_comments", self.news_comments_list)
            item_loader.add_value("create_time", datetime.now())
            item_loader.add_value("crawler_number", 1)
            item = item_loader.load_item()

            print(item)
            yield item
