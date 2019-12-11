"""
过滤关键词
"""
import datetime
from scrapy.exceptions import DropItem
from YuQing.items import NewsItem
import re


class FilterKeywordsPipeline(object):

    def process_item(self, item, spider):
        # print("<--------------FilterKeywordsPipeline---------------->")
        if isinstance(item, NewsItem):
            NewsItemCheck().handel(item, spider)
        return item


class NewsItemCheck(object):

    def handel(self, item, spider):
        self.fields(item, spider)


    def check_key_in_news_title(self, item, key):
        if item.get("newsTitle") is not None:
            return key in item["newsTitle"]
        else:
            return False

    def check_key_in_news_content(self, item, key):
        if item.get("newsContent") is not None:
            return key in item["newsContent"]
        else:
            return False

    def check_key_in_title_and_content(self, item, key):
        """如果key存在新闻里，返回True,否则返回False"""
        return self.check_key_in_news_title(item, key) or self.check_key_in_news_content(item, key)

    def fields(self, item, spider):
        self.EXCEPTION_CONTENT = []
        filter_keywords = item["planDetails"]

        for k, v in filter_keywords.items():
            # 判断排除的词语
            if k == "areas":
                self.check_areas_persons_events(item, "areas", 0)
            if k == "persons":
                self.check_areas_persons_events(item, "persons", 1)
            if k == "events":
                self.check_areas_persons_events(item, "events", 2)
            if k == "exclude":
                self.check_exclude(item, "exclude", 3)
            if k == "planName":
                pass
        else:
            if len(self.EXCEPTION_CONTENT) >0:
                raise DropItem(self.EXCEPTION_CONTENT)

    def check_exclude(self, item, key, index):
        """排除关键词的与或关系判断"""
        key_words = item.get("planDetails").get(key).split(" ")
        key_words_re = item.get("planDetails").get("relationship")[index]

        # 排除关键词为或的关系
        if int(key_words_re) == 0:
            for ex_key in key_words:
                if self.check_key_in_title_and_content(item=item, key=ex_key):
                    self.EXCEPTION_CONTENT.append("本篇新闻【含有】【需要排除】的关键词%s" % item.get("planDetails").get(key))

        # 排除关键词为且的关系
        else:
            ei = 0
            ex_flag = True  # 假设排除的关键词全部在文章里
            while ei < len(key_words):
                if self.check_key_in_title_and_content(item=item, key=key_words[ei]):
                    ex_flag = ex_flag and True
                else:
                    ex_flag = ex_flag and False
                    break
                ei += 1
            if ex_flag:
                self.EXCEPTION_CONTENT.append("本篇新闻【含有】【需要排除】的全部关键词%s" % item.get("planDetails").get(key))

    def check_areas_persons_events(self, item, key, index):
        """判断地域、人物、事件的与或关系"""
        key_words = item.get("planDetails").get(key).split(" ")
        key_words_re = item.get("planDetails").get("relationship")[index]

        # 关键词之间为或的关系
        if int(key_words_re) == 0:
            need_key_times = 0
            for need_key in key_words:
                if self.check_key_in_title_and_content(item=item, key=need_key):
                    need_key_times += 1
                    break
            if need_key_times <= 0:
                self.EXCEPTION_CONTENT.append("本篇新闻【不存在】【需要含有】的关键词%s" % item.get("planDetails").get(key))
        # 关键词之间为且的关系
        else:
            ei = 0
            ex_flag = True  # 假设排除的关键词全部在文章里
            while ei < len(key_words):
                if self.check_key_in_title_and_content(item=item, key=key_words[ei]):
                    ex_flag = ex_flag and True
                else:
                    ex_flag = ex_flag and False
                ei += 1

            if not ex_flag:
                self.EXCEPTION_CONTENT.append("本篇新闻【没有】【需要含有】的全部关键词%s" % item.get("planDetails").get(key))
