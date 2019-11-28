# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 18:02:03 2019
@author: liuty
@e-mail: liuty66@163.com
@introduction:
            解析时间模块
"""
import re
import datetime


class FormatTime(object):

    def format_str_time(self, str_date):
        str_date = str_date.strip()
        time = re.findall(r"([\d]{1,2}):([\d]{1,2}):?[\d]{0,2}", str_date)
        year = 2018
        month = 1
        day = 1
        if (len(str_date) > 11):
            str_date = str_date[:11]
        if (str_date.find('-') > 0):
            year = str_date[:4]
            if (year.isdigit()):
                year = int(year)
            else:
                year = 0

            month = str_date[5:str_date.rfind('-')]
            if (month.isdigit()):
                month = int(month)
            else:
                month = 0

            if (str_date.find(' ') == -1):
                day = str_date[str_date.rfind('-') + 1:]
            else:
                day = str_date[str_date.rfind('-') + 1:str_date.find(' ')]
            if (day.isdigit()):
                day = int(day)
            else:
                day = 0
        elif (str_date.find('年') > 0):
            year = str_date[:4]
            if (year.isdigit()):
                year = int(year)
            else:
                year = 0
            month = str_date[5:str_date.rfind('月')]
            if (month.isdigit()):
                month = int(month)
            else:
                month = 0
            day = str_date[str_date.rfind('月') + 1:str_date.rfind('日')]
            if (day.isdigit()):
                day = int(day)
            else:
                day = 0
        elif (str_date.find('/') > 0):
            year = str_date[:4]
            if (year.isdigit()):
                year = int(year)
            else:
                year = 0
            month = str_date[5:str_date.rfind('/')]
            if (month.isdigit()):
                month = int(month)
            else:
                month = 0
            if (str_date.find(' ') == -1):
                day = str_date[str_date.rfind('/') + 1:]
            else:
                day = str_date[str_date.rfind('/') + 1:str_date.find(' ')]
            if (day.isdigit()):
                day = int(day)
            else:
                day = 0
        else:
            year = 1900
            month = 1
            day = 1
        if month < 10:
            month = '0' + str(month)
        if day < 10:
            day = '0' + str(day)

        if len(time) > 0 :
            time_new = ":".join(time[0])
            time_new = '%s-%s-%s' % (year, month, day) + " " + time_new
            if len(time[0]) > 2:
                return datetime.datetime.strptime(time_new, "%Y-%m-%d %H:%M:%S")
            if len(time[0]) == 2:
                return datetime.datetime.strptime(time_new, "%Y-%m-%d %H:%M")

        return datetime.datetime.strptime('%s-%s-%s' % (year, month, day), "%Y-%m-%d")

    def format_time_stamp(self, time_stamp):
        return datetime.datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M:%S')
