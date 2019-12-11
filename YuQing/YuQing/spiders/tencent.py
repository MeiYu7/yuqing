# -*- coding: utf-8 -*-
import json
from YuQing.utils.format_time import FormatTime
import scrapy
from datetime import datetime
from scrapy import signals
import re
from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader
from YuQing.utils.parse_plan import ParsePlan
import logging


class TencentSpider(scrapy.Spider):
    name = 'tencent'
    allowed_domains = ['sogou.com', 'qq.com']

    start_uri = "qq.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page=1'  # sort 排序方式
    comment_num_temp = "https://coral.qq.com/article/{}/commentnum"
    comment_url_temp = "http://coral.qq.com/article/{}/comment/v2?orinum=30&oriorder=o&cursor={}"

    def __init__(self):
        self.start_time = datetime.now()
        self.news_comments_dict = dict()

    def spider_opened(self):
        logging.info("<------{} spider starting ------>".format(self.start_time))

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
        cls.spider_web_map = settings.get("SPIDERNAME_WEB_MAP")
        cls.project = settings.get("PLAN_PROJECT_SHOW")

    def start_requests(self):
        plans = self.mongo_db[self.col].find({}, projection=self.project)
        for plan in plans:
            logging.info("plan【{}】".format(plan))
            query_word_list = ParsePlan(plan).run()
            for query_word in query_word_list:
                logging.info("query_word【{}】".format(query_word))
                url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
                yield scrapy.Request(url, callback=self.parse, dont_filter=True,
                                     meta={"query_word": query_word, "plan": plan})

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        logging.info("获取【{}】条新闻".format(len(news_list)))
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True,
                                 meta={"plan": response.meta["plan"]})

        # 获取下一页新闻
        next_url = response.xpath("//a[@class='np']/@href").extract_first()
        if next_url is not None:
            next_url = response.urljoin(next_url)
            logging.info("next_url【{}】".format(next_url))
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True,
                                 meta={"plan": response.meta["plan"]})

    def parse_news(self, response):
        # news_id = response.request.url.split('/')[-1].split('.')[0]

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("newsTitle", "//h1/text()")
        item_loader.add_xpath("newsOriTitle", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("newsUrl", response.request.url)
        item_loader.add_xpath("newsTime", "//span[@class='a_time']/text()")
        if not response.xpath("//span[@class='a_time']/text()").extract_first():
            item_loader.add_xpath("newsTime", "//meta[@name='apub:time']/@content")
        item_loader.add_value("newsSource", self.spider_web_map.get(self.name))
        item_loader.add_xpath("newsReportedDepartment", "//span[@class='a_source']//text()")
        item_loader.add_xpath("newsReporter", "//span[@class='a_author']/text()")
        item_loader.add_xpath("newsContent",
                              "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_value("newsEditor", re.findall(r"editor:'(.*?)'", response.body.decode(response.encoding)))
        item_loader.add_value("newsKeyword", re.findall(r"tags:(\[.*?\]),", response.body.decode(response.encoding)))
        item_loader.add_value("planName", response.meta["plan"]["planName"])
        item_loader.add_value("planDetails", response.meta["plan"])
        item = item_loader.load_item()

        comment_ids = re.findall(r'cmt_id[ =]+(\d+);|"comment_id": "(\d+)"', response.body.decode(response.encoding))
        if len(comment_ids) > 0:
            for cmt_id in comment_ids[0]:
                if cmt_id != "":
                    item["newsId"] = cmt_id
                    self.news_comments_dict[cmt_id] = []
                    num_url = self.comment_num_temp.format(cmt_id)
                    yield scrapy.Request(num_url, callback=self.parse_comment_num, meta={"item": item})

        else:
            item["newsComments"] = self.news_comments_dict[item["newsId"]]
            yield item

    def parse_comment_num(self, response):
        """获取评论的总数量"""
        data = json.loads(response.body.decode(response.encoding))
        try:
            comment_total_num = int(data.get("data").get("commentnum"))
        except:
            comment_total_num = 0
        item_loader = NewsItemLoader(item=response.meta["item"])
        item_loader.add_value("newsCommentsNum", comment_total_num)
        item = item_loader.load_item()

        if comment_total_num == 0:
            item["newsComments"] = self.news_comments_dict[item["newsId"]]
            yield item
        else:
            yield scrapy.Request(self.comment_url_temp.format(item["newsId"], 0),
                                 callback=self.parse_comment,
                                 meta={"item": item})

    def parse_one_comment(self, comment_loader, comment, data=None):
        comment_loader.add_value("commentId", comment["id"])
        comment_loader.add_value("parentId", comment["parent"])
        comment_loader.add_value("commentTime", FormatTime().format_time_stamp(int(comment["time"])))
        comment_loader.add_value("content", comment["content"])
        comment_loader.add_value("supportCount", comment["up"])
        comment_loader.add_value("againstCount", "")
        comment_loader.add_value("reviewersId", comment["userid"])
        comment_loader.add_value("reviewersNickname", data["userList"][comment["userid"]]["nick"])
        comment_loader.add_value("reviewersAddr", data["userList"][comment["userid"]]["region"])
        comment_dict = comment_loader.load_item()
        return comment_dict

    def parse_comment(self, response):
        """获取评论信息"""
        item = response.meta["item"]
        # 获取新闻id
        news_id = item["newsId"]
        # 获取总评论数量
        comment_total_num = item["newsCommentsNum"]
        logging.info("{}新闻，获取总评论数量【{}】".format(news_id, comment_total_num))
        # 获取全部页码数量
        # total_page_no = item["news_comments_total_page_no"]

        data = json.loads(response.body.decode(response.encoding))
        data = data.get("data")

        # 获取当前评论页码
        now_page_no = data.get("last")

        # todo 评论有一点问题，评论的添加
        # 获取评论内容
        if len(data.get("oriCommList")) > 0:
            for comment in data.get("oriCommList"):
                comment_loader = NewsItemLoader(item=CommentsItem(), response=response)
                comment_dict = self.parse_one_comment(comment_loader, comment, data)
                # todo 列表的添加
                self.news_comments_dict[news_id].append(comment_dict)
        logging.info("{}新闻，{}条评论，获取了{}条".format(news_id, comment_total_num, len(self.news_comments_dict[news_id])))

        # 获取下一页
        if now_page_no != "":
            next_comment_url = self.comment_url_temp.format(item["newsId"], now_page_no)
            yield scrapy.Request(next_comment_url, callback=self.parse_comment, meta={"item": item})

        # 保存
        if len(self.news_comments_dict[news_id]) >= comment_total_num:
            item["newsComments"] = self.news_comments_dict[news_id]

            yield item
