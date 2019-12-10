"""
解析舆情计划，对应与或关系，返回爬虫搜索字符串list
"""
import datetime
import re
import itertools


class ParsePlan(object):
    def __init__(self, plan):

        self.areas = plan["areas"]
        self.persons = plan["persons"]
        self.events = plan["events"]
        self.relationship = plan["relationship"]
        self.areas_re = self.relationship[:1]
        self.persons_re = self.relationship[1:2]
        self.events_re = self.relationship[2:3]
        self.query_list = []

    def parse(self):
        """解析与或关系"""
        areas_list = re.split(" ", self.areas)
        areas_list = self.and_or_relation(areas_list, self.areas_re)
        persons_list = re.split(" ", self.persons)
        persons_list = self.and_or_relation(persons_list, self.persons_re)
        events_list = re.split(" ", self.events)
        events_list = self.and_or_relation(events_list, self.events_re)

        self.parse_combinations(areas_list, persons_list, events_list)

    def and_or_relation(self, key_list, keys_re):

        if len(key_list) > 0 and int(keys_re) > 0:
            return "\" \"".join(key_list),

        elif len(key_list) == 0:
            return None
        else:
            return key_list

    def parse_combinations(self, areas_list, persons_list, events_list):

        for a in range(1, len(areas_list) + 1):
            for ai in itertools.combinations(areas_list, a):

                for p in range(1, len(persons_list) + 1):
                    for pi in itertools.combinations(persons_list, p):

                        for e in range(1, len(events_list) + 1):
                            for ei in itertools.combinations(events_list, e):
                                rest = []
                                if ai[0] != "":
                                    rest += list(ai)
                                if pi[0] != "":
                                    rest += list(pi)
                                if ei[0] != "":
                                    rest += list(ei)

                                query_word = "\"" + "\" \"".join(rest) + "\""
                                self.query_list.append(query_word)

    def run(self):
        self.parse()
        return self.query_list


if __name__ == '__main__':
    plan = {'planName': '方案一',
            'areas': '河南 扶沟',
            'persons': '李主任',
            'events': '投诉 告状 打人',
            'exclude': '广告',
            'relationship': '0001',
            'createTime': datetime.datetime(2019, 12, 10, 6, 33, 50, 571000),
            'updateTime': datetime.datetime(2019, 12, 10, 6, 33, 50, 571000),
            '_class': 'com.yzkj.zf.entity.Plan'
            }

    p = ParsePlan(plan["areas"], plan["persons"], plan['events'], plan['exclude'], plan['relationship'])
    res = p.run()
    # print(res)
    i = 1
    for r in res:
        print(i, r)
        i += 1
