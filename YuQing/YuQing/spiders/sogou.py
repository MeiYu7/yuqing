# -*- coding: utf-8 -*-
import json

import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem, CommentsItem
from YuQing.loaders.loader import NewsItemLoader, NewsCommentsItemLoader


class SogouSpider(scrapy.Spider):
    name = 'sogou'
    allowed_domains = ['sogou.com', 'sohu.com']
    # start_urls = ['http://sogou.com/']
    start_uri = "sohu.com"
    sogou_url_temp = 'https://news.sogou.com/news?query=site:{0} {1}&sort=1&page={2}'  # sort 排序方式
    souhu_read_url = 'http://v2.sohu.com/public-api/articles/{}/pv'
    comment_url_temp = "http://apiv2.sohu.com/api/comment/list?&page_size=30&page_no={page}&source_id=mp_{new_id}"
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
        spider = super(SogouSpider, cls).from_crawler(crawler, *args, **kwargs)
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
            query_word = plan["areas"] + plan["events"]
            print(query_word)
            url = self.sogou_url_temp.format(self.start_uri, query_word, "1")
        # query_word = 'site:sohu.com 杀人'
        # page = 1
        # url = self.sogou_url_temp.format(query_word, page)
            print(url)
            yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={"query_word": query_word})

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True)

        # 先获取最大页码，再去循环
        max_page = response.xpath("//div[@id='pagebar_container']/a[last()-1]/text()").extract_first()
        print(max_page)
        if max_page is not None:
            for i in range(2, int(max_page)+1):
                next_url = self.sogou_url_temp.format(self.start_uri, response.meta["query_word"], str(i))
                print(next_url)
                yield scrapy.Request(next_url, callback=self.parse, dont_filter=False, meta={"query_word": response.meta["query_word"]})

        # next_url = response.xpath("//a[@class='np']/@href").extract_first()
        # print("next_url=========>",next_url)
        # if next_url is not None:
        #     next_url = response.urljoin(next_url)
        #     print('=====>', next_url)
        #     yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)

    def parse_news(self, response):
        new_id = response.request.url.split('/')[-1].split('_')[0]

        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//article/p[@data-role='original-title']/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time", "//div[@class='article-info']//span[@class='time']/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department", "//div[@class='user-info']//h4/a/text()")
        item_loader.add_xpath("news_reporter",
                              "//article/p[(position()=last()-1 or position()<3) and contains(text(),'记者')]/text()")
        item_loader.add_xpath("news_content", "//article/p[position()>1 and position()<last()]//text()")
        item_loader.add_xpath("news_editor", "//article/p[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_xpath("news_keyword", "//a[@class='tag']/text()")
        item_loader.add_value("news_comments", [])
        item = item_loader.load_item()

        yield scrapy.Request(self.souhu_read_url.format(new_id), callback=self.parse_readnum,
                             meta={"item": item, "new_id": new_id})

    def parse_readnum(self, response):

        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("news_read_num", response.body.decode("utf-8"))
        item = item_loader.load_item()
        self.item += 1

        # 下面获取评论数据
        comment_url = self.comment_url_temp.format(page="1", new_id=response.meta["new_id"])
        yield scrapy.Request(comment_url, callback=self.parse_comment,
                             meta={"item": item, "new_id": response.meta["new_id"]})

    def parse_comment(self, response):

        data = json.loads(response.body.decode(response.encoding))

        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("news_comments_num", data["jsonObject"]["cmt_sum"])

        # 获取评论内容
        if data["jsonObject"]["cmt_sum"] != 0:
            comments = data["jsonObject"]["comments"]

            for comment in comments:
                comment_loader = NewsCommentsItemLoader(item=CommentsItem())
                comment_loader.add_value("comment_id", comment["comment_id"])
                comment_loader.add_value("content", comment["content"])
                comment_loader.add_value("comment_time", datetime.fromtimestamp(int(str(comment["create_time"])[:-3])))
                comment_loader.add_value("support_count", comment["support_count"])
                comment_loader.add_value("against_count", "")
                comment_loader.add_value("reviewers_id", comment["user_id"])
                comment_loader.add_value("reviewers_addr", comment["ip_location"])
                comment_loader.add_value("reviewers_nickname", comment["passport"]["nickname"])

                comment_dict = comment_loader.load_item()
                # todo 列表的添加
                self.news_comments_list.append(comment_dict)

        total_page_no = int(data["jsonObject"]["total_page_no"])

        if total_page_no >= 2:
            for i in range(2, total_page_no+1):
                next_comment_url = self.comment_url_temp.format(page=str(i), new_id=response.meta["new_id"])
                yield scrapy.Request(next_comment_url, callback=self.parse_comment,
                                 meta={"item": item, "new_id": response.meta["new_id"]})

        if len(self.news_comments_list) == data["jsonObject"]["cmt_sum"]:
            item_loader.add_value("news_comments", self.news_comments_list)
            item_loader.add_value("create_time", datetime.now())
            item_loader.add_value("crawler_number", 1)
            item = item_loader.load_item()

            # print(item)
            yield item
