# 处理sogou验证码
import time

from scrapy.http import HtmlResponse


class AntispiderRequestMiddleware(object):
    def __init__(self, settings):
        self.browser = settings.get('seleniumBrowser')

    @classmethod
    def from_settings(cls, settings):
        o = cls(settings)
        return o

    def process_request(self, request, spider):
        if "antispider" in request.url:
            print("Sogou正在进行验证码验证， 程序休眠半小时")
            time.sleep(60 * 30)
            # 休息30秒 手动输入验证码
            # self.browser.get(request.url)
            # time.sleep(60)
            # 返回加载后的页面response
            return HtmlResponse(url=request.url, body=self.browser.page_source,
                                encoding="utf-8", request=request)
