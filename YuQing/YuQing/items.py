# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item,Field
from scrapy.loader.processors import Compose,MapCompose,Join

from YuQing.loaders.processors import *


class NewsItem(Item):
    collection_exception = 'exception_field'

    news_title = Field(input_processor=MapCompose(str.strip))   # 新闻标题
    news_ori_title = Field(input_processor=MapCompose(str_replace))  # 新闻原标题
    news_url = Field()
    news_time = Field(input_processor=Compose(deal_time))    # 新闻发布时间
    news_source = Field(input_processor=MapCompose(split_url))  # 新闻来源
    news_reported_department = Field()  # 新闻报道部门
    news_reporter= Field(input_processor=Compose(deal_author))  # 记者
    news_content = Field(input_processor=Compose(delete_blank))  # 新闻内容
    news_editor = Field(input_processor=MapCompose(str_replace))   # 责任编辑
    news_keyword = Field(input_processor=Compose(delete_blank))  # 关键词

    news_read_num = Field()  # 阅读人数
    news_comments_num = Field()  # 评论人数
    news_comments = Field()  # 新闻评论内容

    plan_name = Field()
    error = Field()

class CommentsItem(Item):
    """评论列表"""


class ErrorItem(Item):
    """出现异常的spider数据"""
    collection = 'exception_spider'
    title = Field()
    url = Field()
    type = Field()
    content = Field()
    time = Field()


class StatsItem(Item):
    """数据收集"""
    collection = 'scrapy_stats'

    start_time = Field()
    finish_time = Field()
    finish_reason = Field()
    item_scraped_count = Field()
    response_received_count = Field()
    item_dropped_count = Field()
    item_dropped_reasons_count = Field()
    finaly_insert_item = Field()
    finaly_find_ids = Field()
    time_secodes_consum = Field()