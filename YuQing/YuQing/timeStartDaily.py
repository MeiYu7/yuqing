# 文件timerStartDaily.py
from scrapy import cmdline
import datetime
import time
import shutil
import os
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class TimeStartDaily(object):

    def __init__(self):
        self.recoderDir = r"crawls"   # 这是为了爬虫能够续爬而创建的目录，存储续爬需要的数据
        self.checkFile = "isRunning.txt"  # 爬虫是否在运行的标志
        self.startTime = datetime.datetime.now()
        print(f"startTime = {self.startTime}")

    def run(self):
        i = 0
        miniter = 0
        while True:
            isRunning = os.path.isfile(self.checkFile)
            if not isRunning:                       # 爬虫不在执行，开始启动爬虫
                # 在爬虫启动之前处理一些事情，清掉JOBDIR = crawls
                isExsit = os.path.isdir(self.recoderDir)  # 检查JOBDIR目录crawls是否存在
                print(f"mySpider not running, ready to start. isExsit:{isExsit}")
                if isExsit:
                    removeRes = shutil.rmtree(self.recoderDir)  # 删除续爬目录crawls及目录下所有文件
                    print(f"At time:{datetime.datetime.now()}, delete res:{removeRes}")
                else:
                    print(f"At time:{datetime.datetime.now()}, Dir:{self.recoderDir} is not exsit.")
                time.sleep(5)
                clawerTime = datetime.datetime.now()
                waitTime = clawerTime - self.startTime
                print(f"At time:{clawerTime}, start clawer: mySpider !!!, waitTime:{waitTime}")
                execute("scrapy crawlall".split())

                break
            else:
                print(f"At time:{datetime.datetime.now()}, mySpider is running, sleep to wait.")
            i += 1
            time.sleep(600)        # 每10分钟检查一次
            miniter += 10
            if miniter >= 1440:    # 等待满24小时，自动退出监控脚本
                break


if __name__ == '__main__':
    t = TimeStartDaily()
    t.run()