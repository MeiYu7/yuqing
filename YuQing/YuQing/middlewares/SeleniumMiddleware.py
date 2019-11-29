# 下载中间件，使用用selenium 爬取
import time

from scrapy.http import HtmlResponse
from selenium.common.exceptions import TimeoutException


class SeleniumMiddleware(object):
    def process_request(self, request, spider):
        """处理一切请求的方法"""
        # 这个if条件很重要，用来区分哪个请求使用selenium
        if request.meta.get("middleware") == "SeleniumMiddleware":
            try:
                # url是request自带的属性，可以直接调用请求
                spider.browser.get(request.url)
                # 这个方法是使窗口下拉
                spider.browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            except TimeoutException as e:
                print('超时')
                # 如果请求超时，就停止
                spider.browser.execute_script('window.stop()')
            # 休息2s，使页面加载完全
            time.sleep(2)
            # 返回加载后的页面response
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding="utf-8", request=request)