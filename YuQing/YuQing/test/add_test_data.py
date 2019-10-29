"""
脚本：
添加舆情方案到mongodb
"""
import time
import threading
import pymongo
from faker import Faker
from datetime import datetime


class AddTestData(object):

    def __init__(self):
        self.f = Faker(locale='zh_CN')
        self.data_list = []
        self.time_start = datetime.now()
        self._client = pymongo.MongoClient("mongodb://localhost:27017")
        self._db = self._client["test"]
        self.col = self._db["news"]

    def add_data(self, n=20):
        """添加计划"""
        self.j = 0
        self.n = n
        for i in range(n):
            data = {
                "news_url": self.f.url(),
                "news_content": self.f.text(),
                "news_keyword": self.f.words(),
                "news_ori_title": self.f.sentence(),
                "news_reported_department": "",
                "news_reporter": self.f.name(),
                "news_source": "",
                "news_time": self.f.date(),
                "news_title": self.f.sentence(),
                "comments": []
            }
            for u in range(self.f.random_int()):
                comment_item = {
                    "content": self.f.sentence(),
                    "comment_id": self.f.random_number(digits=8),
                    "comment_time": self.f.date()
                }
                data["comments"].append(comment_item)
            else:
                self.j += 1
                self.data_list.append(data)

                print("已有{}data".format(len(self.data_list)))

    def insert_data(self):
        while 1:
            self.time_end = datetime.now()
            if (self.time_end - self.time_start).seconds >= 100:
                self.time_start = self.time_end
                self.insert_mongo()

            if self.j == self.n:
                self.insert_mongo()
                break
            time.sleep(5)
            print("sleep 5s")

    def insert_mongo(self):
        if len(self.data_list) > 0:
            ret = self.col.insert_many(self.data_list, ordered=False)
            self.data_list = []
            insert_ids_num = len(ret.inserted_ids)
            print("{}时间 插入{}条".format(self.time_end, insert_ids_num))

    def run(self):
        # 多线程
        t1 = threading.Thread(target=self.add_data, args=(1000000,))
        t2 = threading.Thread(target=self.insert_data)
        for t in [t1, t2]:
            t.start()

        for t in [t1, t2]:
            t.join()

        print("all done")


if __name__ == '__main__':
    ap = AddTestData()
    ap.run()
