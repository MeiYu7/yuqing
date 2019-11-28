import os
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# execute('scrapy crawl sogou'.split(" "))
# execute('scrapy crawl tencent'.split(" "))
# execute('scrapy crawl news'.split(" "))
# execute('scrapy crawl test'.split(" "))
# execute('scrapy crawl sina'.split(" "))
# execute('scrapy crawl ifeng'.split(" "))
# execute('scrapy crawl neteasy'.split(" "))
# execute('scrapy crawl neteasy_1'.split(" "))
# execute('scrapy crawl people'.split(" "))
execute('scrapy crawl sohu'.split(" "))