import datetime
from scrapy.exceptions import DropItem
from YuQing.items import NewsItem


class FieldCheckPipeline(object):

    def process_item(self, item, spider):
        if isinstance(item, NewsItem):
            NewsItemCheck().handel(item, spider)
        return item


class NewsItemCheck(object):

    def handel(self, item, spider):
        self.fields(item, spider)

    def fields(self, item, spider):
        f = spider.settings.get('CHECK_FIELDS')  # settings配置字段，需要检查的字段类型为列表
        if not f:
            f = ['news_time', 'news_content', 'news_title']
        EXCEPTION_FIELD = '字段%s异常;异常类型:%s;异常内容:%s'
        EXCEPTION_CONTENT = []
        for i in f:
            if i == "news_time":
                time_date = item.get(i)
                filter_time = spider.settings.get("FILTER_TIME")
                if isinstance(time_date, str) and int(time_date[:4]) <= int(filter_time[:4]):
                    EXCEPTION_CONTENT.append(EXCEPTION_FIELD % (i, type(time_date), "时间小于预定值"))
                if isinstance(time_date, datetime.datetime) and time_date <= datetime.datetime.strptime(filter_time,"%Y-%m-%d"):
                    EXCEPTION_CONTENT.append(EXCEPTION_FIELD % (i, type(time_date), "时间小于预定值"))
            else:
                if item.get(i) == "":
                    EXCEPTION_CONTENT.append(EXCEPTION_FIELD % (i, type(None), item.get(i)))

        if EXCEPTION_CONTENT != []:
            raise DropItem(EXCEPTION_CONTENT)
