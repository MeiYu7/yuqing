# -*- coding: utf-8 -*-
import json
import re

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class NeteasySpider(scrapy.Spider):
    name = 'neteasy'
    allowed_domains = ['163.com', 'sogou.com']

    start_uri = "163.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式
    comment_url_temp = "http://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/{news_id}/comments/newList?limit=30&showLevelThreshold=72&offset={page}"

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
        spider = super(NeteasySpider, cls).from_crawler(crawler, *args, **kwargs)
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
        news_id = response.request.url.split("/")[-1].split(".")[0]
        self.news_comments_dict[news_id] = []

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_value("news_id", news_id)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time",
                              "//div[@class='post_time_source' or @class='headline' or @class='text']/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department",
                              "//div[contains(@class, 'source')]/a[contains(@id,'source')]/text()")
        item_loader.add_xpath("news_reporter", "//p[contains(text(), '记者')]/text()")
        # item_loader.add_xpath("news_content", "//div[contains(@class, 'text') or contains(@class,'viewport')]//p/text()")
        item_loader.add_xpath("news_editor", "//span[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_value("news_keyword", "")
        item_loader.add_value("news_comments", [])
        item_loader.add_value("plan_name", response.meta["plan_name"])
        item = item_loader.load_item()

        yield scrapy.Request("http://comment.tie.163.com/{}.html".format(news_id), callback=self.parse_comment_num,
                             meta={"item": item})

    def parse_comment_num(self, response):
        """获取评论的总数量"""
        item = response.meta["item"]
        news_id = item["news_id"]
        comment_total_num = re.findall('"tcount":(.*?),"title"', response.body.decode(response.encoding))[0]
        print(comment_total_num)

        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("news_comments_num", comment_total_num)
        item = item_loader.load_item()

        # 如果没有评论，就保存item
        if comment_total_num == 0:
            print("parse_comment_num  保存！ 保存！ 保存！")
            item["news_comments"] = self.news_comments_dict[news_id]
            item["create_time"] = datetime.now()
            item["crawler_number"] = 1

            yield item
        else:
            comment_url = self.comment_url_temp.format(news_id=item["news_id"], page="0")
            yield scrapy.Request(comment_url, callback=self.parse_comment, meta={"item": item},
                                 dont_filter=True)

    def parse_one_comment(self, comment_loader, comment):
        comment_loader.add_value("comment_id", comment["commentId"])
        comment_loader.add_value("content", comment["content"])
        comment_loader.add_value("comment_time", comment["createTime"])
        comment_loader.add_value("support_count", comment["vote"])
        comment_loader.add_value("against_count", comment["against"])
        comment_loader.add_value("reviewers_id", comment["user"]["userId"])
        comment_loader.add_value("reviewers_addr", comment["user"].get("location"))
        comment_loader.add_value("reviewers_nickname", comment["user"].get("nickname"))
        comment_loader.add_value("parent_id", "")
        comment_dict = comment_loader.load_item()

        return comment_dict

    def parse_parent_id_order(self, parent_id_list, comment_id):
        try:
            i = parent_id_list.index(comment_id)
            return parent_id_list[: i-1]
        except Exception as e:
            print(e)
            return "0"

    def parse_comment(self, response):
        """获取评论信息"""
        item = response.meta["item"]
        # 获取新闻id
        news_id = item["news_id"]
        # 获取总评论数量
        comment_total_num = item["news_comments_num"]
        print("comment_total_num", type(comment_total_num))
        # 获取全部页码数量
        total_page_no = item["news_comments_total_page_no"]

        # 获取当前评论页码
        now_page_no = re.findall(r"offset=(\d+?)", response.request.url)
        if len(now_page_no) > 0:
            now_page_no = int(now_page_no[0]) // 30
        else:
            now_page_no = 0

        data = json.loads(response.body.decode(response.encoding))

        for comment_ids in data["commentIds"]:
            for comment_id in comment_ids.split(","):
                comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                comment_loader.add_value("parent_id", self.parse_parent_id_order(comment_ids, comment_id))
                comment_dict = self.parse_one_comment(comment_loader, data["comments"][comment_id])
                self.news_comments_dict[news_id].append(comment_dict)

        # 获取下一页
        next_page_no = now_page_no + 1
        if next_page_no <= total_page_no:
            next_comment_url = self.comment_url_temp.format(news_id=item["news_id"], page=str(next_page_no * 30))
            yield scrapy.Request(next_comment_url, callback=self.parse_comment, meta={"item": item})

        # 保存 todo 获取的评论会大于新闻数量，暂时先这样做
        if len(self.news_comments_dict[news_id]) >= comment_total_num:
            print("parse_comment   保存！ 保存！ 保存！")
            item["news_comments"] = self.news_comments_dict[news_id]
            item["create_time"] = datetime.now()
            item["crawler_number"] = 1

            yield item
