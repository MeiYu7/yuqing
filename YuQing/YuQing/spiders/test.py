# -*- coding: utf-8 -*-
import scrapy


class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['baobeihuijia.com']
    start_urls = ['']

    def parse(self, response):
        print(response.request.url)
