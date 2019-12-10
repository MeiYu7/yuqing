# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field
from scrapy.loader.processors import Compose, MapCompose, Join,Identity

from YuQing.loaders.processors import *


class NewsItem(Item):
    collection_exception = 'exceptionField'

    newsUrl = Field()
    newsId = Field()  # 新增news_id
    newsTitle = Field(input_processor=MapCompose(str.strip))  # 新闻标题
    newsOriTitle = Field(input_processor=MapCompose(str_replace))  # 新闻原标题
    newsTime = Field(input_processor=Compose(deal_time))  # 新闻发布时间
    newsSource = Field(input_processor=MapCompose(split_url))  # 新闻来源
    newsReportedDepartment = Field()  # 新闻报道部门
    newsReporter = Field(output_processor=Compose(str_replace), input_processor=Compose(deal_author))  # 记者
    newsContent = Field(input_processor=Compose(delete_blank))  # 新闻内容
    newsEditor = Field(input_processor=MapCompose(str_replace))  # 责任编辑
    newsKeyword = Field(input_processor=Compose(delete_blank))  # 关键词

    newsReadNum = Field(input_processor=MapCompose(str_to_int))  # 阅读人数
    newsCommentsNum = Field(input_processor=MapCompose(str_to_int))  # 评论人数
    newsComments = Field(out_processor=Identity())  # 新闻评论内容
    newsCommentsTotalPageNo = Field()  # 新增
    planName = Field()
    planDetails = Field()

    crawlerNumber = Field()  # 爬虫次数，最多3次
    createTime = Field()  # 爬虫更新时间，最多3条
    updateTime = Field()  # 爬虫更新时间，最多3条

    error = Field()


class CommentsItem(Item):
    """评论列表"""
    commentId = Field()  # 评论id
    content = Field(input_processor=MapCompose(str_replace))  # 评论内容
    commentTime = Field(input_processor=MapCompose(deal_time))  # 评论时间
    supportCount = Field()  # 评论支持数(点赞)
    againstCount = Field()  # 评论反对数(踩)
    reviewersId = Field()  # 评论者id
    reviewersAddr = Field(input_processor=MapCompose(str_replace))  # 评论者所属地
    reviewersNickname = Field(input_processor=MapCompose(str_replace))  # 评论者昵称
    parentId = Field()  # 父级评论id串，以减号"-"相隔


class ErrorItem(Item):
    """出现异常的spider数据"""
    collection = 'exceptionSpider'
    title = Field()
    url = Field()
    type = Field()
    content = Field()
    time = Field()


class StatsItem(Item):
    """数据收集"""
    collection = 'scrapyStats'

    startTime = Field()
    finishTime = Field()
    finishReason = Field()
    itemScrapedCount = Field()
    responseReceivedCount = Field()
    itemDroppedCount = Field()
    # itemDroppedReasons = Field()
    finalyInsertItem = Field()
    finalFindIds = Field()
    # timeSecodesConsNum = Field()
