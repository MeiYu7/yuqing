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

    start_uri = "people.com.cn"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式

    comment_url_temp = "http://bbs1.people.com.cn/post/1/0/2/{news_id}_{page}.html"

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
        """解析新闻"""
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
        # item_loader.add_value("news_comments", [])
        item_loader.add_value("plan_name", response.meta["plan_name"])
        item = item_loader.load_item()

        comment_url = response.xpath("//div[@class='message']/a/@href").extract_first()
        if comment_url is not None:
            yield scrapy.Request(comment_url, callback=self.parse_comment_num, meta={"item": item}, dont_filter=True)
        else:
            # yield item
            print("parse_news 保存 保存 保存")

    def parse_comment_num(self, response):
        # news_id 在跳转的评论页获取
        news_id = response.request.url.split("/")[-1].split(".")[0]
        self.news_comments_dict[news_id] = []
        news_comments_num = re.findall(r'class="replayNum">(\d+)</span>', response.body.decode(response.encoding))
        if len(news_comments_num)>0:
            news_comments_num = news_comments_num[0]
        else:
            news_comments_num = 0

        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item, response=response)
        item_loader.add_value("news_id", news_id)
        item_loader.add_xpath("news_read_num", "//span[@class='readNum']/text()")
        item_loader.add_xpath("news_comments_total_page_no", "//div[@class='pageBar']/@pagecount")
        item_loader.add_value("news_comments_num", news_comments_num)
        item = item_loader.load_item()

        if item["news_comments_num"] == "0" or item["news_comments_num"] == 0:
            print("parse_comment_num  保存！ 保存！ 保存！")
            item["news_comments"] = self.news_comments_dict[news_id]
            item["create_time"] = datetime.now()
            item["crawler_number"] = 1
            # print(item)
            yield item
        else:
            print(item)
            yield scrapy.Request(self.comment_url_temp.format(news_id=news_id, page="1"), callback=self.parse_comment,
                                 meta={"item": item}, dont_filter=True)

    def parse_one_comment(self, comment_loader, comment=None, data=None):
        comment_loader.add_xpath("reviewers_nickname", "./p/a[@class='userNick']/text()")
        comment_loader.add_xpath("content", "./p/a[@class='treeReply']/text()")
        comment_dict = comment_loader.load_item()
        return comment_dict

    def parse_comment(self, response):
        """获取评论信息"""
        item = response.meta["item"]
        # 获取新闻id
        news_id = item["news_id"]
        # 获取总评论数量
        comment_total_num = item["news_comments_num"]
        # 获取全部评论页码
        total_page_no = item.get("news_comments_total_page_no") if item.get("news_comments_total_page_no") else 0

        # 获取当前评论页码
        now_page_no = response.request.url.split("_")[-1].split(".")[0]
        if len(now_page_no) > 0:
            now_page_no = int(now_page_no[0])
        else:
            now_page_no = 1

        # 获取评论内容
        li_list = response.xpath("//ul[@class='subUL']/li")
        if len(li_list) > 0:
            for li in li_list:
                comment_loader = NewsCommentsItemLoader(item=CommentsItem(), selector=li)
                comment_dict = self.parse_one_comment(comment_loader)
                # 列表的添加
                self.news_comments_dict[news_id].append(comment_dict)

        print("{}新闻，{}条评论，获取了{}条".format(news_id, comment_total_num, len(self.news_comments_dict[news_id])))

        # 获取下一页
        next_page_no = now_page_no + 1
        if next_page_no <= total_page_no:
            next_comment_url = self.comment_url_temp.format(page=str(next_page_no), news_id=item["news_id"])
            yield scrapy.Request(next_comment_url, callback=self.parse_comment, meta={"item": item})

        # 保存 todo 如果本页没有获取到数据怎么办？
        if len(self.news_comments_dict[news_id]) >= comment_total_num:
            print("parse_comment   保存！ 保存！ 保存！")
            item["news_comments"] = self.news_comments_dict[news_id]
            item["create_time"] = datetime.now()
            item["crawler_number"] = 1

            yield item
