

# 随机使用user_agent
from faker import Faker


class RandomUseragentMiddleware(object):
    def __init__(self):
        # self.ua = UserAgent()
        self.f = Faker(locale='zh_CN')

    def process_request(self, request, spider):
        # useragent = self.ua.random
        useragent = self.f.user_agent()
        # print(useragent)
        request.headers.setdefault('User-Agent', useragent)