# -*- coding: utf-8 -*-
import json
import re
import time

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class Neteasy1Spider(scrapy.Spider):
    name = 'neteasy_1'
    allowed_domains = ['163.com', "baidu.com", "people.com.cn"]
    start_urls = ['https://www.baidu.com/']

    def __init__(self):
        self.news_comments_dict = dict()
        self.comment_id_list = list()
        self.times = 0

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        # print("抓到{}个新闻".format(self.item))
        pass

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(Neteasy1Spider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        cls.allowed_domains.extend(settings.get('ALLOWED_DOMAINS'))
        cls.mongo_db = settings.get("DB_MONGO")
        cls.col = settings.get("DB_PLAN")

        # def start_requests(self):
        query_word = '杀人'
        # url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
        # print(url)
        # yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={"query_word": query_word})

    # def parse(self, response):
    #     item_loader = NewsItemLoader(item=NewsItem(), response=response)
    #
    #     item_loader.add_value("try_name", {"name": "333"})
    #     item_loader.add_value("try_name", {"name": "2222"})
    #     item_loader.add_value("try_name", {"name": "1111"})
    #     # print(item_loader)
    #     item = item_loader.load_item()
    #     print("1--->",item)
    #     # print(item)
    #     print("**********************")
    #
    #     yield scrapy.Request("https://www.baidu.com/", callback=self.parse_2, dont_filter=True, meta={"item": item})
    #
    # def parse_2(self, response):
    #     item = response.meta["item"]
    #     print(item)
    #     item_loader = NewsItemLoader(item=item)
    #
    #     print("***************************")
    #     item_loader.add_value("try_name", item["try_name"])
    #     item_loader.add_value("try_name", {"name": "444"})
    #     item_loader.add_value("try_name", {"name": "555"})
    #     item_loader.add_value("try_name", {"name": "666"})
    #
    #     item = item_loader.load_item()
    #     print("2--->",item)

    # def start_requests(self):
    #
    #     yield scrapy.Request("https://www.baidu.com/", callback=self.parse, dont_filter=True)

    def parse(self, response):
        print("parse==>", response.request.url)
        # item_loader = NewsItemLoader(item=NewsItem(), response=response)
        # item_loader.add_value("plan_name", 8)
        # item = item_loader.load_item()
        item = {}
        item["plan_name"] = 8
        item["news_id"] = "174066775"
        self.news_comments_dict[item["news_id"]] = []
        item["news_comments"] = self.news_comments_dict[item["news_id"]]

        print(id(item["news_comments"]))
        print("*******************************")
        print(item)
        yield scrapy.Request("http://bbs1.people.com.cn/post/1/0/2/173572749_1.html#replyList",
                             callback=self.parse_comment, dont_filter=True,
                             meta={"item": item, "news_id": item["news_id"]})

    def parse_comment(self, response):
        print("parse_read_num===>", response.request.url)
        item = response.meta["item"]
        news_id = response.meta["news_id"]
        comment_id = response.request.url.split("/")[-1].split("_")[0]
        now_page = response.request.url.split("_")[-1].split(".")[0]
        print(now_page)

        comment_num = response.xpath("//span[@class='replayNum']/text()").extract_first()
        print(comment_num)
        if comment_num is None:
            comment_num = 400

        total_page_no = response.xpath("//div[@class='pageBar']/@pagecount").extract_first()

        item_loader = NewsItemLoader(item=item, response=response)

        item_loader.add_xpath("news_read_num", "//span[@class='readNum']/text()")
        item_loader.add_xpath("news_comments_num", "//span[@class='replayNum']/text()")
        # item_loader.add_value("news_comments", item["news_comments"])
        # item = item_loader.load_item()
        # comments
        if int(comment_num) > 0:
            li_list = response.xpath("//ul[@class='subUL']/li")
            print("获取到多少条评论--》", len(li_list))  # todo 有时获取不到评论
            if len(li_list) == 0:
                print("write a html")
                with open("111.html", "wb") as f:
                    f.write(response.body)
            for li in li_list:
                # 单条评论
                comment_loader = NewsCommentsItemLoader(item=CommentsItem(), selector=li)
                comment_loader.add_xpath("reviewers_nickname", "./p/a[@class='userNick']/text()")
                comment_loader.add_xpath("content", "./p/a[@class='treeReply']/text()")
                comment_dict = comment_loader.load_item()
                # print(comment_dict)
                # todo 评论的链接问题
                self.news_comments_dict[item["news_id"]].append(comment_dict)


        # else:
        #
        print("此时收集多少评论——————》", len(self.news_comments_dict[item["news_id"]]))
        print("*************************************************")
        # print(item)

        # 结束条件
        if len(self.news_comments_dict[item["news_id"]]) >= int(comment_num):
            item_loader.add_value("news_comments_num", comment_num)
            item_loader.add_value("news_comments", self.news_comments_dict[item["news_id"]])  #  todo 取全部列表
            item_loader.add_value("create_time", datetime.now())
            item_loader.add_value("crawler_number", 1)
            item = item_loader.load_item()
            # item["news_comments"] = self.news_comments_dict[item["news_id"]]

            print(item)
            # yield item

        # 获取下一页评论
        # now_page = response.xpath("//input[@name='pageNo']/@value").extract_first()

        if now_page and total_page_no and int(now_page) <= int(total_page_no):
            next_comment_url = response.request.url.replace("_" + str(now_page), "_" + str(int(now_page)+1))
            print("next_page", next_comment_url)
            yield scrapy.Request(next_comment_url, callback=self.parse_comment, meta={"item": item, "news_id": news_id}, dont_filter=True)
