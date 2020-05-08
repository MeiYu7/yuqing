# -*- coding: utf-8 -*-
import json
import re

import scrapy
from datetime import datetime
from scrapy import signals
import logging
from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader
from YuQing.utils.parse_plan import ParsePlan


class SohuSpider(scrapy.Spider):
    name = 'sohu'
    allowed_domains = ['sogou.com', 'sohu.com']

    start_uri = "sohu.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式
    souhu_read_url = 'http://v2.sohu.com/public-api/articles/{}/pv'
    comment_url_temp = "http://apiv2.sohu.com/api/comment/list?&page_size=30&page_no={page}&source_id=mp_{news_id}"

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
        kwargs.pop('_job')
        cls.from_settings(crawler.settings)
        spider = super(SohuSpider, cls).from_crawler(crawler, *args, **kwargs)
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
        news_id = response.request.url.split('/')[-1].split('_')[0]
        self.news_comments_dict[news_id] = []

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_value("newsId", news_id)
        item_loader.add_xpath("newsTitle", "//h1/text()")
        item_loader.add_xpath("newsOriTitle", "//article/p[@data-role='original-title']/text()")
        item_loader.add_value("newsUrl", response.request.url)
        item_loader.add_xpath("newsTime", "//div[@class='article-info']//span[@class='time']/text()")
        item_loader.add_value("newsSource", self.spider_web_map.get(self.name))
        item_loader.add_xpath("newsReportedDepartment", "//div[@class='user-info']//h4/a/text()")
        item_loader.add_xpath("newsReporter",
                              "//article/p[(position()=last()-1 or position()<3) and contains(text(),'记者')]/text()")
        item_loader.add_xpath("newsContent", "//article/p[position()>1 and position()<last()]//text()")
        item_loader.add_xpath("newsEditor", "//article/p[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_xpath("newsKeyword", "//a[@class='tag']/text()")
        # item_loader.add_value("newsComments", [])
        item_loader.add_value("planName", response.meta["plan"]["planName"])
        item_loader.add_value("planDetails", response.meta["plan"])
        item = item_loader.load_item()
        # print(item)
        yield scrapy.Request(self.souhu_read_url.format(news_id), callback=self.parse_read_num, meta={"item": item})

    def parse_read_num(self, response):
        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("newsReadNum", response.body.decode("utf-8"))
        item = item_loader.load_item()

        # 下面获取评论数据
        comment_url = self.comment_url_temp.format(page="1", news_id=item["newsId"])
        yield scrapy.Request(comment_url, callback=self.parse_comment_num, meta={"item": item})

    def parse_comment_num(self, response):
        """获取评论的总数量"""
        item = response.meta["item"]
        news_id = item["newsId"]
        data = json.loads(response.body.decode(response.encoding))
        # 获取总评论数量
        comment_total_num = int(data["jsonObject"]["cmt_sum"])
        logging.info("{}新闻，获取总评论数量【{}】".format(news_id,comment_total_num))

        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("newsCommentsNum", comment_total_num)
        item_loader.add_value("newsCommentsTotalPageNo", int(data["jsonObject"]["total_page_no"]))
        item = item_loader.load_item()

        # 如果没有评论，就保存item
        if comment_total_num == 0:
            item["newsComments"] = self.news_comments_dict[news_id]
            # print(item)
            yield item
        else:
            yield scrapy.Request(response.request.url, callback=self.parse_comment, meta={"item": item},
                                 dont_filter=True)

    def parse_one_comment(self, comment_loader, comment, data=None):
        comment_loader.add_value("commentId", comment["comment_id"])
        comment_loader.add_value("parentId", "")
        comment_loader.add_value("commentTime", datetime.fromtimestamp(int(str(comment["create_time"])[:-3])))
        comment_loader.add_value("content", comment["content"])
        comment_loader.add_value("supportCount", comment["support_count"])
        comment_loader.add_value("againstCount", "")
        comment_loader.add_value("reviewersId", comment["user_id"])
        comment_loader.add_value("reviewersNickname", comment["passport"]["nickname"])
        comment_loader.add_value("reviewersAddr", comment["ip_location"])

        # 本条评论有父级评论
        if len(comment["comments"]) > 0:
            parent_comment_loader = NewsCommentsItemLoader(item=CommentsItem())
            comment_dict = self.parse_one_comment(parent_comment_loader, comment)



        comment_dict = comment_loader.load_item()

        return comment_dict

    def parse_comment(self, response):
        """获取评论信息"""
        item = response.meta["item"]
        # 获取新闻id
        news_id = item["newsId"]
        # 获取总评论数量
        comment_total_num = item["newsCommentsNum"]
        logging.info("{}新闻，获取总评论数量【{}】".format(news_id,comment_total_num))
        # 获取全部页码数量
        total_page_no = item["newsCommentsTotalPageNo"]

        # 获取当前评论页码
        now_page_no = re.findall(r"page_no=(\d+)", response.request.url)
        if len(now_page_no) > 0:
            now_page_no = int(now_page_no[0])
        else:
            now_page_no = 1

        data = json.loads(response.body.decode(response.encoding))

        # 获取评论内容
        if len(data["jsonObject"]["comments"]) > 0:
            for comment in data["jsonObject"]["comments"]:
                comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                comment_dict = self.parse_one_comment(comment_loader, comment)
                # todo 列表的添加
                self.news_comments_dict[news_id].append(comment_dict)

        logging.info("{}新闻，{}条评论，获取了{}条".format(news_id, comment_total_num, len(self.news_comments_dict[news_id])))
        # 获取下一页
        next_page_no = now_page_no + 1
        if next_page_no <= total_page_no:
            next_comment_url = self.comment_url_temp.format(page=str(next_page_no), news_id=item["newsId"])
            yield scrapy.Request(next_comment_url, callback=self.parse_comment, meta={"item": item})

        # 保存
        if len(self.news_comments_dict[news_id]) >= comment_total_num:
            item["newsComments"] = self.news_comments_dict[news_id]
            yield item
