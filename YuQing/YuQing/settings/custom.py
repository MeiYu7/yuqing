NEWS_FILE = './utils/news_xpath2.csv'

ALLOWED_DOMAINS = ['sogou.com', 'qq.com', 'sohu.com', 'sina.com.cn', 'ifeng.com', '163.com', 'people.com.cn']

# 爬虫对应的网站
SPIDERNAME_WEB_MAP = {
    "sohu": "搜狐网",
    "tencent": "腾讯网",
    "sina": "新浪网",
    "people": "人民网",
    "neteasy": "网易新闻",
    "ifeng": "凤凰网",
}

# 舆情方案查询的字段
PLAN_PROJECT_SHOW = {"_id": False, "planName": True, "areas": True, "events": True, "exclude": True, "persons": True, "relationship": True}

CHECK_FIELDS = ['newsTime', 'newsContent', 'newsTitle']

TEST_KEYWORD = '河南'

FILTER_TIME = "2018-1-1"

# scrapy-redis 配置  所有信息每次都要重新请求，所以暂时不用布隆过滤
# SCHEDULER = "YuQing.lib.scrapy_redis_bloomfilter.scheduler.Scheduler"  # BoolFilter调度器
# DUPEFILTER_CLASS = "YuQing.lib.scrapy_redis_bloomfilter.dupefilter.RFPDupeFilter"  # BoolFilter过滤器
# BLOOMFILTER_HASH_NUMBER = 6  # BoolFilter生成的hash函数的个数
# BLOOMFILTER_BIT = 30  # BoolFilter位数组大小 2 * 30次方， 约暂用redis内存128M
# SCHEDULER_PERSIST = True  # redis持久化

# Redis URL
REDIS_URL = 'redis://localhost:6379'

# 配置搜狗Cookie池的地址
SOGOU_COOKIES_URL = 'http://localhost:5022/sogou/random'

# Mongo URL
MONGO_URI = 'mongodb://60.190.243.103:27222'
MONGO_DATABASE = 'yuqings'
COLLECTION_NEWS = 'warningInfo'
MONGODB_ERROR = "scrapyError"
DB_PLAN = 'plan'
STATS_COLLECTION = 'scrapyStats'

DOWNLOAD_TIMEOUT = 60  # 请求时间达到多少秒重试
RETRY_ENABLED = True  # 开启重试
RETRY_TIMES = 3  # 重试3次

FEED_EXPORT_ENCODING = 'utf-8'  # 输出中文的编码格式

# 日志模块
# to_day = datetime.datetime.now()
# log_file_path = "./log/scrapy_{}_{}_{}.log".format(to_day.year,to_day.month, to_day.day)
LOG_LEVEL = "INFO"
# LOG_FILE = log_file_path

"""保存数据的频率"""
SAVE_TIME_INTERVAL = 60
SAVE_ITEM_CAPACITY = 100

# 自定义过滤条件
DONT_FILTER_REQUEST = False
