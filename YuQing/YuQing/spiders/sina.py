# -*- coding: utf-8 -*-
import json
import re

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class SinaSpider(scrapy.Spider):
    name = 'sina'
    allowed_domains = ['sina.com.cn', 'sogou.com']
    # start_urls = ['http://sina.com.cn/']

    start_uri = "sina.com.cn"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式

    comment_url_temp = "http://comment.sina.com.cn/page/info?format=json&channel={0}&newsid={1}&ie=utf-8&oe=utf-8&page={2}&page_size=100"
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
        spider = super(SinaSpider, cls).from_crawler(crawler, *args, **kwargs)
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
            query_word = "杀人"
            url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
            print(url)
            yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={"query_word": query_word})

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True)

        # 先获取最大页码，再去循环
        max_page = response.xpath("//div[@id='pagebar_container']/a[last()-1]/text()").extract_first()
        if max_page is not None:
            for i in range(2, int(max_page) + 1):
                next_url = self.sogou_url_temp.format(self.start_uri, response.meta["query_word"], str(i))
                yield scrapy.Request(next_url, callback=self.parse, dont_filter=False,
                                     meta={"query_word": response.meta["query_word"]})

    def parse_news(self, response):
        """解析新浪新闻"""

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time",
                              "//div[contains(@class,'article-header') or @class='date-source']//span/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department",
                              "//div[contains(@class,'article-header') or @class='date-source']//span/following-sibling::*//text()")
        item_loader.add_xpath("news_reporter", "//p[contains(text(), '记者')]/text()")
        item_loader.add_xpath("news_content", "//div[@class='article' or @class='article-body main-body']//p//text()")
        item_loader.add_xpath("news_editor", "//p[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_xpath("news_keyword", "//div[contains(@class,'keywords') or contains(@class,'tag')]//a/text()")
        item_loader.add_value("news_comments", [])
        item = item_loader.load_item()
        # print(item)

        # comments
        gn_comos = response.xpath("//meta[@name='comment']/@content").extract_first()
        if gn_comos is not None:
            comment_url = self.comment_url_temp.format(gn_comos.split(":")[0], gn_comos.split(":")[1], "1")
            yield scrapy.Request(comment_url, callback=self.parse_comment, meta={"item": item, "gn_comos": gn_comos})

        comos = response.xpath("//p[@class='source-time']//b[@class='mcom_num']/@data-comment").extract_first()
        if comos is not None:
            gn = re.findall(r'"channel":"(.*?)"', response.body.decode(response.encoding))[0]
            comment_url = self.comment_url_temp.format(gn, comos, "1")
            yield scrapy.Request(comment_url, callback=self.parse_comment,
                                 meta={"item": item, "gn_comos": gn + ":" + comos})

    def parse_comment(self, response):
        print("requesting...... comment==>", response.request.url)
        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)

        data = json.loads(response.body.decode(response.encoding))

        if data["result"]["status"]["msg"] != "":
            comment_num = 0
        else:
            comment_num = data["result"]["count"]["show"]

        total_page_no = comment_num // 100 + 1

        if comment_num != 0 and len(data["result"]["cmntlist"]) > 0:

            for comment in data.get("result").get("cmntlist"):
                comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                comment_loader.add_value("comment_id", comment["mid"])
                comment_loader.add_value("content", comment["content"])
                comment_loader.add_value("comment_time", comment["time"])
                comment_loader.add_value("support_count", comment["agree"])
                comment_loader.add_value("against_count", "")
                comment_loader.add_value("reviewers_id", comment["uid"])
                comment_loader.add_value("reviewers_addr", comment["area"])
                comment_loader.add_value("reviewers_nickname", comment["nick"])
                comment_loader.add_value("parent_id", comment["parent"])

                comment_dict = comment_loader.load_item()
                # 列表的添加
                self.news_comments_list.append(comment_dict)

        if total_page_no >= 2:
            for i in range(2, total_page_no + 1):
                next_comment_url = self.comment_url_temp.format(response.meta["gn_comos"].split(":")[0],
                                                                  response.meta["gn_comos"].split(":")[1],
                                                                  str(i))

                yield scrapy.Request(next_comment_url, callback=self.parse_comment,
                                     meta={"item": item, "gn_comos": response.meta["gn_comos"]})

        if len(self.news_comments_list) == comment_num:
            item_loader.add_value("news_comments_num", comment_num)
            item_loader.add_value("news_comments", self.news_comments_list)
            item_loader.add_value("create_time", datetime.now())
            item_loader.add_value("crawler_number", 1)
            item = item_loader.load_item()

            print(item)
            yield item
