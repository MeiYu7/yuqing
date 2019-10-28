"""
脚本：
添加舆情方案到mongodb
"""
import pymongo


class AddPlans(object):

    def __init__(self, plan_name, areas, persons, events, exclude):
        self.plan_name = plan_name
        self.areas = areas
        self.persons = persons
        self.events = events
        self.exclude = exclude

    def connect_mongo(self):
        """链接mongodb"""
        self._client = pymongo.MongoClient("mongodb://localhost:27017")
        self._db = self._client["yuqings"]
        self.col = self._db["plans"]

    def add_plan(self):
        """添加计划"""; self.connect_mongo()
        data = {
            "plan_name": self.plan_name,
            "areas": self.areas,
            "persons": self.persons,
            "events": self.events,
            "exclude": self.events

        }
        self.col.insert_one(data)


if __name__ == '__main__':
    plan_name = "方案一"
    areas = "河南&扶沟"
    persons = ""
    events = ""
    exclude = "广告"

    ap = AddPlans(plan_name, areas, persons, events, exclude)
    ap.add_plan()
