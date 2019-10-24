import os
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# execute('scrapy crawl sogou'.split(" "))
# execute('scrapy crawl tencent'.split(" "))
execute('scrapy crawl news'.split(" "))
# execute('scrapy crawl test'.split(" "))