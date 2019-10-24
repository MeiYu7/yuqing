
NEWS_FILE = 'C:/Users\myq91\Desktop\MYQSpiders\YuQing\YuQing//utils/news_xpath2.csv'

ALLOWED_DOMAINS = ['sogou.com','qq.com','sohu.com','sina.com.cn','ifeng.com','163.com','people.com.cn']

TEST_KEYWORD = '杭州'

FILTER_TIME = 2018

# scrapy-redis 配置
SCHEDULER = "YuQing.lib.scrapy_redis_bloomfilter.scheduler.Scheduler"  # BoolFilter调度器
DUPEFILTER_CLASS = "YuQing.lib.scrapy_redis_bloomfilter.dupefilter.RFPDupeFilter"  # BoolFilter过滤器
BLOOMFILTER_HASH_NUMBER = 6  # BoolFilter生成的hash函数的个数
BLOOMFILTER_BIT = 30  # BoolFilter位数组大小 2 * 30次方， 约暂用redis内存128M
SCHEDULER_PERSIST = True  # redis持久化

# Redis URL
REDIS_URL = 'redis://localhost:6379'

# Mongo URL
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'yuqings'
COLLECTION_NEWS = 'news'
MONGODB_ERROR = "scrapy_error"
DB_PLAN = 'plans'
STATS_COLLECTION = 'scrapy_stats'


DOWNLOAD_TIMEOUT = 30  # 请求时间达到多少秒重试
RETRY_ENABLED = True  # 开启重试
RETRY_TIMES = 3  # 重试3次


FEED_EXPORT_ENCODING ='utf-8'  # 输出中文的编码格式


# 日志模块
# to_day = datetime.datetime.now()
# log_file_path = "./log/scrapy_{}_{}_{}.log".format(to_day.year,to_day.month, to_day.day)
# LOG_LEVEL = "DEBUG"
# LOG_FILE = log_file_path

"""保存数据的频率"""
SAVE_TIME_INTERVAL = 60
SAVE_ITEM_CAPACITY = 100

# 自定义过滤条件
DONT_FILTER_REQUEST = False