# -*- coding: utf-8 -*-
import json
from YuQing.utils.format_time import FormatTime
import scrapy
from datetime import datetime
from scrapy import signals
import re
from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class TencentSpider(scrapy.Spider):
    name = 'tencent'
    allowed_domains = ['sogou.com', 'qq.com']

    start_uri = "qq.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page=1'  # sort 排序方式
    comment_num_temp = "https://coral.qq.com/article/{}/commentnum"
    comment_url_temp = "http://coral.qq.com/article/{}/comment/v2?orinum=30&oriorder=o&cursor={}"

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
        spider = super(TencentSpider, cls).from_crawler(crawler, *args, **kwargs)
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
            # query_word = plan["areas"] + plan["events"] + plan["persons"]
            query_word = "杀人"
            plan_name = plan["plan_name"]
            print(query_word)
            url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
            print(url)
            yield scrapy.Request(url, callback=self.parse, dont_filter=True,
                                 meta={"query_word": query_word, "plan_name": plan_name})

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        print("获取{}条新闻".format(len(news_list)))
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True,
                                 meta={"plan_name": response.meta["plan_name"]})

        # 获取下一页新闻
        next_url = response.xpath("//a[@class='np']/@href").extract_first()
        print("next_url=========>", next_url)
        if next_url is not None:
            next_url = response.urljoin(next_url)
            print('=====>', next_url)
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True,
                                 meta={"plan_name": response.meta["plan_name"]})

    def parse_news(self, response):
        news_id = response.request.url.split('/')[-1].split('.')[0]
        self.news_comments_dict[news_id] = []

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time", "//span[@class='a_time']/text()")
        if not response.xpath("//span[@class='a_time']/text()").extract_first():
            item_loader.add_xpath("news_time", "//meta[@name='apub:time']/@content")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department", "//span[@class='a_source']//text()")
        item_loader.add_xpath("news_reporter", "//span[@class='a_author']/text()")
        item_loader.add_xpath("news_content",
                              "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_value("news_editor", re.findall(r"editor:'(.*?)'", response.body.decode(response.encoding)))
        item_loader.add_value("news_keyword", re.findall(r"tags:(\[.*?\]),", response.body.decode(response.encoding)))
        item_loader.add_value("plan_name", response.meta["plan_name"])
        item = item_loader.load_item()

        comment_ids = re.findall(r'cmt_id[ =]+(\d+);|"comment_id": "(\d+)"', response.body.decode(response.encoding))
        if len(comment_ids) > 0:
            for cmt_id in comment_ids[0]:
                if cmt_id != "":
                    num_url = self.comment_num_temp.format(cmt_id)
                    yield scrapy.Request(num_url, callback=self.parse_comment_num, meta={"item": item, "cmt_id": cmt_id})

        else:
            print("本篇新闻没有评论")
            yield item

    def parse_comment_num(self, response):
        data = json.loads(response.body.decode(response.encoding))
        comment_num = int(data.get("data").get("commentnum"))
        item_loader = NewsItemLoader(item=response.meta["item"])
        item_loader.add_value("news_comments_num", comment_num)
        item = item_loader.load_item()

        yield scrapy.Request(self.comment_url_temp.format(response.meta["cmt_id"], 0),
                             callback=self.parse_comment,
                             meta={"item": item, "cmt_id": response.meta["cmt_id"], "news_comments_num": comment_num})

    def parse_comment(self, response):
        """解析评论"""
        print(response.request.url)
        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)
        data = json.loads(response.body.decode(response.encoding))
        last_page = data.get("data").get("last")
        data = data.get("data")
        comment_num = int(data["targetInfo"]["commentnum"])
        # todo 评论有一点问题，评论的添加
        for comment in data.get("oriCommList"):
            cmt_item_loader = NewsItemLoader(item=CommentsItem(), response=response)
            cmt_item_loader.add_value("comment_id", comment["id"])
            cmt_item_loader.add_value("parent_id", comment["parent"])
            cmt_item_loader.add_value("comment_time", FormatTime().format_time_stamp(int(comment["time"])))
            cmt_item_loader.add_value("content", comment["content"])
            cmt_item_loader.add_value("support_count", comment["up"])
            cmt_item_loader.add_value("against_count", "")
            cmt_item_loader.add_value("reviewers_id", comment["userid"])
            cmt_item_loader.add_value("reviewers_nickname", data["userList"][comment["userid"]]["nick"])
            cmt_item_loader.add_value("reviewers_addr", data["userList"][comment["userid"]]["region"])
            cmt_item = cmt_item_loader.load_item()
            self.news_comments_list.append(cmt_item)

        if last_page != "":
            next_url = self.comment_url_temp.format(response.meta["cmt_id"], last_page)
            yield scrapy.Request(next_url, callback=self.parse_comment,
                                 meta={"item": item, "cmt_id": response.meta["cmt_id"], "news_comments_num": response.meta["news_comments_num"]})

        print(comment_num)
        if len(self.news_comments_list) == comment_num:
            item_loader.add_value("news_comments", self.news_comments_list)
            item_loader.add_value("create_time", datetime.now())
            item_loader.add_value("crawler_number", 1)
            item = item_loader.load_item()
            # print(item)
            yield item
