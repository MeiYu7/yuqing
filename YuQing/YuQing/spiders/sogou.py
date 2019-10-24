# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from scrapy import signals

from YuQing.items import NewsItem
from YuQing.loaders.loader import NewsItemLoader

class SogouSpider(scrapy.Spider):
    name = 'sogou'
    allowed_domains = ['sogou.com','sohu.com']
    # start_urls = ['http://sogou.com/']
    sogou_url_temp = 'https://news.sogou.com/news?query={}&sort=1&page={}'  # sort 排序方式
    souhu_read_url = 'http://v2.sohu.com/public-api/articles/{}/pv'
    item = 0

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        print("抓到{}个新闻".format(self.item))


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(SogouSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        # cls.mongo_db = settings.get("DB_MONGO")
        # cls.cate_brand = settings.get("CATE_COLLECTION")
        pass

    def start_requests(self):
        query_word = 'site:sohu.com 扶沟县'
        page = 1
        url = self.sogou_url_temp.format(query_word,page)
        print(url)
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        news_list = response.xpath("//div[@class='results']/div//h3/a")
        for a in news_list:
            a_href = a.xpath("./@href").extract_first()
            yield scrapy.Request(a_href, callback=self.parse_news)


        next_url = response.xpath("//a[@id='sogou_next']/@href").extract_first()
        if next_url:
            next_url = response.urljoin(next_url)
            print('=====>',next_url)
            yield scrapy.Request(next_url,callback=self.parse)

    def parse_news(self,response):
        new_id = response.request.url.split('/')[-1].split('_')[0]

        item_loader = NewsItemLoader(item=NewsItem(),response=response)
        item_loader.add_xpath("news_title","//h1/text()")
        item_loader.add_xpath("news_ori_title","//article/p[@data-role='original-title']/text()")
        item_loader.add_value("news_url", response.request.url)
        item_loader.add_xpath("news_time","//div[@class='article-info']//span[@class='time']/text()")
        item_loader.add_value("news_source",response.request.url)
        item_loader.add_xpath("news_reported_department","//div[@class='user-info']//h4/a/text()")
        item_loader.add_xpath("news_reporter","//article/p[(position()=last()-1 or position()<3) and contains(text(),'记者')]/text()")
        item_loader.add_xpath("news_content","//article/p[position()>1 and position()<last()]//text()")
        item_loader.add_xpath("news_editor","//article/p[contains(text(),'责任编辑') or contains(text(),'责编')]/text()")
        item_loader.add_xpath("news_keyword","//a[@class='tag']/text()")
        item = item_loader.load_item()

        yield scrapy.Request(self.souhu_read_url.format(new_id), callback=self.parse_readnum,meta={"item":item})

    def parse_readnum(self, response):

        item = response.meta["item"]
        item_loader = NewsItemLoader(item=item)
        item_loader.add_value("news_read_num",response.body.decode("utf-8"))
        # item_loader.add_xpath("news_comments_num","//div[@class='c-comment-header clear']//span[2]/text()")
        # item_loader.add_xpath("news_comments","")
        item = item_loader.load_item()
        print(item)
        self.item += 1

        # yield item