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
    # start_urls = ['http://qq.com/']
    sogou_url_temp = 'https://news.sogou.com/news?query={}&sort=1&page={}'  # sort 排序方式
    # souhu_read_url = 'http://v2.sohu.com/public-api/articles/{}/pv'
    comment_num_temp = "https://coral.qq.com/article/{}/commentnum"
    comment_list_temp = "http://coral.qq.com/article/{}/comment/v2?orinum=30&oriorder=o&cursor={}"
    item = 0

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        print("抓到{}个新闻".format(self.item))

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(TencentSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        # cls.mongo_db = settings.get("DB_MONGO")
        # cls.cate_brand = settings.get("CATE_COLLECTION")
        pass

    def start_requests(self):
        query_word = 'site:qq.com 比特币'
        page = 1
        url = self.sogou_url_temp.format(query_word, page)
        print(url)
        yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news, dont_filter=True)

        next_url = response.xpath("//a[@id='sogou_next']/@href").extract_first()
        if next_url:
            next_url = response.urljoin(next_url)
            print('下一页=====>', next_url)
            yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)

    def parse_news(self, response):
        new_id = response.request.url.split('/')[-1].split('_')[0]
        item_loader = NewsItemLoader(item=NewsItem(), response=response)
        item_loader.add_xpath("news_title", "//h1/text()")
        item_loader.add_xpath("news_ori_title", "//p[contains(text(), '原标题')]/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time", "//span[@class='a_time']/text()")
        item_loader.add_value("news_source", response.request.url)
        item_loader.add_xpath("news_reported_department", "//span[@class='a_source']//text()")
        item_loader.add_xpath("news_reporter", "//span[@class='a_author']/text()")
        item_loader.add_xpath("news_content",
                              "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_xpath("news_content",
                              "//div[contains(@class,'content') or @bosszone='content']//p[not(script) and not(style)]//text()")
        item_loader.add_value("news_editor", re.findall(r"editor:'(.*?)'", response.body.decode(response.encoding)))
        item_loader.add_value("news_keyword", re.findall(r"tags:(\[.*?\]),", response.body.decode(response.encoding)))
        item = item_loader.load_item()

        comment_ids = re.findall(r'cmt_id[ =]+(\d+);|"comment_id": "(\d+)"', response.body.decode(response.encoding))
        if len(comment_ids) > 0:
            for cmt_id in comment_ids[0]:
                if cmt_id != "":
                    num_url = self.comment_num_temp.format(cmt_id)
                    yield scrapy.Request(num_url, callback=self.parse_comment_num,
                                         meta={"item": item, "cmt_id": cmt_id})

        else:
            # yield item
            print("本篇新闻没有评论")
            pass

    def parse_comment_num(self, response):
        data = json.loads(response.body.decode(response.encoding))
        comment_num = int(data.get("data").get("commentnum"))
        item_loader = NewsItemLoader(item=response.meta["item"])
        item_loader.add_value("news_comments_num", comment_num)
        item = item_loader.load_item()

        yield scrapy.Request(self.comment_list_temp.format(response.meta["cmt_id"], 0),
                             callback=self.parse_comment,
                             meta={"item": item, "cmt_id": response.meta["cmt_id"]})

    def parse_comment(self, response):
        """解析评论"""
        print(response.request.url)
        item_loader = NewsItemLoader(item=response.meta["item"])
        data = json.loads(response.body.decode(response.encoding))
        last_page = data.get("data").get("last")
        data = data.get("data")
        # todo 评论有一点问题，评论的添加
        comment_list = []
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
            comment_list.append(cmt_item)

        item_loader.add_value("news_comments", comment_list)
        item = item_loader.load_item()
        print("=====>", item)

        if last_page != "":
            next_url = self.comment_list_temp.format(response.meta["cmt_id"], last_page)
            print("下一页评论", next_url)

            yield scrapy.Request(next_url, callback=self.parse_comment,
                                 meta={"item": item, "cmt_id": response.meta["cmt_id"]})
