# -*- coding: utf-8 -*-
import scrapy


class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['sogou.com']
    start_urls = ['https://weixin.sogou.com/antispider/?from=%2fweixin%3Ftype%3d2%26query%3d%E6%97%A5%E6%9C%AC%E5%A4%A7%E9%98%AA%E5%9C%B0%E9%9C%87']


    def parse(self, response):
        print(response.request.url)


