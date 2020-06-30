# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 18:02:03 2019
@author: liuty
@e-mail: liuty66@163.com
@introduction:
            解析时间模块
"""
import re
from datetime import datetime, timezone, timedelta


class FormatTime(object):

    def format_str_time(self, str_date):
        str_date_new = str_date.strip()
        time_new = ""
        time = re.findall(r"([\d]{1,2}):([\d]{1,2}):?[\d]{0,2}", str_date)
        if len(time) == 0:
            time_new = "00:00:00"
        if len(time) > 0:
            time_new = ":".join(time[0])
            if len(time[0]) == 2:
                time_new += ":00"

        if len(time) > 0:
            time1 = ":".join(time[0])
            time_index = str_date.find(time1)
            str_date_new = str_date[:time_index].strip()

        if str_date_new.find("-") > 0:
            str_date_new = self.deal_link_word(str_date_new, "-", "-", None)

        elif str_date.find('年') > 0:
            str_date_new = self.deal_link_word(str_date_new, "年", "月", "日")

        elif str_date.find('/') > 0:
            str_date_new = self.deal_link_word(str_date_new, "/", "/", None)

        else:
            str_date_new = '%s-%s-%s' % (2018, 1, 1)

        total_time = str_date_new + " " + time_new

        return total_time

    def deal_link_word(self, word, link1, link2, link3):
        str_date_new = word
        year = 2018
        month = 1
        day = 1
        if str_date_new.find(link1) > 0:
            index1 = str_date_new.find(link1)
            year = str_date_new[:index1]
            if year.isdigit():
                year = int(year)
            else:
                year = 0
            index2 = str_date_new.rfind(link2)
            month = str_date_new[index1 + 1:index2]
            if month.isdigit():
                month = int(month)
            else:
                month = 0
            if link3:
                day = str_date_new[index2 + 1:str_date_new.rfind(link3)]
            else:
                day = str_date_new[index2 + 1:]
            if day.isdigit():
                day = int(day)
            else:
                day = 1
            if month < 10:
                month = '0' + str(month)
            if day < 10:
                day = '0' + str(day)
        return '%s-%s-%s' % (year, month, day)

    def format_time_stamp(self, time_stamp):
        return datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M:%S')

    def str_to_datetime(self, time_str):
        try:
            time_str = self.format_str_time(time_str)
            ret = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
        except Exception as e:
            raise e
        return ret


if __name__ == '__main__':
    f = FormatTime()
    s = f.str_to_datetime("2020/01/28 14:33")
    print(s)