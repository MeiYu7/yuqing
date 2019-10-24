import re
from YuQing.utils.format_time import format_time

def str_replace(values):
    if isinstance(values, list):
        values = values[0]
        values = re.sub(r"\s", " ", values)
    value = re.sub(r'[0-9a-zA-Z_（）\(\)]+|来源:|责任编辑：|原标题：|\u3000|\u200b|\u200b|\xa0|返回搜狐，查看更多|扫一扫，用手机看新闻！|用微信扫描还可以|分享至好友和朋友圈|相关视频：|\[|\]|[\n\t\r]+ ',"",values).strip()
    return value

def delete_blank(values):
    """删除空格"""
    if isinstance(values, list):
        if len(values)>0 and values[0].startswith("[") and values[0].endswith("]"):
            try:
                return " ".join([str_replace(v.strip()) for v in eval(values[0])])
            except:
                return values[0]
        else:
            return " ".join([str_replace(v.strip()) for v in values])


split_url = lambda x:x.split("/")[2]

def deal_author(values,loader_context):
    author_name = set()
    if isinstance(values, list):
        for value in values:
            if len(value)>30:
                value = re.findall(r'[(（]记者(.*?)[)）]', value)
                if len(value)>0:
                    author_name.add(value[0])
            else:
                if '记者' in value:
                    value = re.findall(r'记者(.*)', value)
                    if len(value) > 0:
                        author_name.add(value[0])
                else:
                    author_name.add(value)

    return ''.join(list(author_name))

def deal_time(values):
    value = values
    if isinstance(values, list):
        if len(values)>0:
            values = values[0]
            values = re.sub(r"\s", " ", values)
            value = re.sub(r'来源|[\[\]\n\t\r]+|\u3000|\u200b|\u200b|：',"",values).strip()
            value = format_time(value)

    return value

