"""
时间转换
"""
from YuQing.items import NewsItem, CommentsItem
from YuQing.utils.format_time import FormatTime


class ConvertTimeType(object):

    def process_item(self, item, spider):
        if isinstance(item, NewsItem):
            NewsItemCheck().handel(item, spider)
        return item


class NewsItemCheck(object):

    def handel(self, item, spider):
        if item.get("newsTime") is not None and isinstance(item.get("newsTime"), str):
            try:
                item["newsTime"] = FormatTime().str_to_datetime(item.get("newsTime"))
            except Exception as e:
                raise e

        if len(item.get("newsComments")) > 0:

            for comments in item["newsComments"]:
                if comments.get("commentTime") is not None and isinstance(comments.get("commentTime"), str):
                    try:
                        comments["commentTime"] = FormatTime().str_to_datetime(comments.get("commentTime"))
                    except Exception as e:
                        raise e

