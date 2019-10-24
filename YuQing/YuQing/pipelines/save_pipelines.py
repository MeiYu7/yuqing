# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from datetime import datetime
import pymongo
from YuQing.items import NewsItem
# from scrapy.log import logger


class YuqingPipeline(object):
    def __init__(self,mongo_uri, mongo_db,collection_name,time_interval,item_capacity,stats):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name
        self.time_interval = time_interval
        self.item_capacity = item_capacity
        self.goods_items = []
        self.time_start = datetime.now()
        self.insert_num = 0
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            collection_name = crawler.settings.get('COLLECTION_NEWS', 'news'),
            time_interval = crawler.settings.get("SAVE_TIME_INTERVAL", 60),
            item_capacity = crawler.settings.get("SAVE_ITEM_CAPACITY", 100),
            stats = crawler.stats
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.coll = self.db[self.collection_name]  # 创建数据库中的表格

    def close_spider(self, spider):
        if len(self.goods_items)>0:
            self.insert_many_goods()
        self.client.close()
        print("最终插入{}条".format(self.insert_num))
        self.stats.set_value("finaly_insert_item",self.insert_num )
        logger.info("最终插入{}条".format(self.insert_num))

    def process_item(self, item, spider):
        if isinstance(item,NewsItem):
            self.process_goods_item(item,spider)
        return item

    def process_goods_item(self, item,spider):
        self.goods_items.append(dict(item))
        self.time_end = datetime.now()
        print("此时积攒了item{}个".format(len(self.goods_items)))

        if len(self.goods_items)>= self.item_capacity:
            self.insert_many_goods()

        elif (self.time_end-self.time_start).seconds >= self.time_interval:
            self.insert_many_goods()
            self.time_start = self.time_end

    def insert_many_goods(self):
        ret = self.coll.insert_many(self.goods_items,  ordered=False)
        self.goods_items = []
        insert_ids_num = len(ret.inserted_ids)
        self.insert_num += insert_ids_num
        print("{}时间 插入{}条".format(self.time_end, insert_ids_num))
