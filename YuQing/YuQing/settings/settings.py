# -*- coding: utf-8 -*-

# 添加搜索路径
import os
import sys

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_PATH)
sys.path.append(BASE_PATH + r'/lib')

BOT_NAME = 'YuQing'

SPIDER_MODULES = ['YuQing.spiders']
NEWSPIDER_MODULE = 'YuQing.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'YuQing.middlewares.YuqingSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'YuQing.middlewares.YuqingDownloaderMiddleware.YuqingDownloaderMiddleware': 0,
    'YuQing.middlewares.RandomCookieMiddleware.RandomCookieMiddleware': 50,
    'YuQing.middlewares.ProcessAllExceptionMiddleware.ProcessAllExceptionMiddleware': 100,
    'YuQing.middlewares.MoGuProxyMiddleware.MoGuProxyMiddleware': 100,
    'YuQing.middlewares.AntispiderRequestMiddleware.AntispiderRequestMiddleware': 100,
    'YuQing.middlewares.RandomUseragentMiddleware.RandomUseragentMiddleware': 200,
    # 'YuQing.middlewares.SeleniumMiddleware.SeleniumMiddleware': 300,
    'YuQing.middlewares.StatCollectorMiddleware.StatCollectorMiddleware': 400
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
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

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'YuQing.pipelines.save_pipelines.YuqingPipeline': 300,
    'YuQing.pipelines.field_check.FieldCheckPipeline': 100,
    'YuQing.pipelines.save.MongoDBPipeline': 300

}



CUSTOM_SETTINGS = 'YuQing.settings.custom'

# 自定义过滤条件
DONT_FILTER_REQUEST = True

# # 禁止重定向
# REDIRECT_ENABLED = False