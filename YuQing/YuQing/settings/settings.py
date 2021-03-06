# -*- coding: utf-8 -*-

# 添加搜索路径
import os
import sys
import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_PATH)
sys.path.append(BASE_PATH + r'/lib')

BOT_NAME = 'YuQing'

SPIDER_MODULES = ['YuQing.spiders']
NEWSPIDER_MODULE = 'YuQing.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 3

DOWNLOAD_DELAY = 2

# COOKIES_ENABLED = False

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'YuQing.middlewares.YuqingDownloaderMiddleware.YuqingDownloaderMiddleware': 0,
    'YuQing.middlewares.RandomCookieMiddleware.SogouRandomCookieMiddleWare': 50,
    'YuQing.middlewares.ProcessAllExceptionMiddleware.ProcessAllExceptionMiddleware': 100,
    # 'YuQing.middlewares.MoGuProxyMiddleware.MoGuProxyMiddleware': 100,
    'YuQing.middlewares.AntispiderRequestMiddleware.AntispiderRequestMiddleware': 100,
    'YuQing.middlewares.RandomUseragentMiddleware.RandomUseragentMiddleware': 200,
    # 'YuQing.middlewares.SeleniumMiddleware.SeleniumMiddleware': 300,
    'YuQing.middlewares.StatCollectorMiddleware.StatCollectorMiddleware': 400
}

EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'YuQing.extensions.settings.LoaderCustomSettings': 0,
    'YuQing.extensions.db.MonGoDB': 100,
    'YuQing.extensions.corestats.CoreStats': 110,
    # 'YuQing.extensions.selenium_browser.SeleniumBrowser': 110,
    'YuQing.extensions.requst.BeforeFilterRequest': 0,
    'YuQing.extensions.exception.SpiderExceptionExtension': 140,
    'YuQing.extensions.exception.FieldErrorExtension': 160,
}

ITEM_PIPELINES = {
    # 'YuQing.pipelines.save_pipelines.YuqingPipeline': 300,
    'YuQing.pipelines.field_check.FieldCheckPipeline': 100,
    'YuQing.pipelines.FilterKeyworks.FilterKeywordsPipeline': 200,
    'YuQing.pipelines.convert_time_type.ConvertTimeType': 210,
    'YuQing.pipelines.save.MongoDBPipeline': 300

}

CUSTOM_SETTINGS = 'YuQing.settings.custom'

# 自定义过滤条件
DONT_FILTER_REQUEST = True

# # 禁止重定向
# REDIRECT_ENABLED = False

# 启动全部爬虫配置
COMMANDS_MODULE = 'YuQing.commands'

# 日志模块
to_day = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
log_file_path = "./log/scrapy_{}_{}.log".format(to_day.year, to_day.month)
LOG_LEVEL = "WARNING"
LOG_FILE = log_file_path