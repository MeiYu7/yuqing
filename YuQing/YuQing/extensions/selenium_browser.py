from selenium import webdriver


class SeleniumBrowser(object):

    def __init__(self,settings):
        # Chrome浏览器
        options = webdriver.ChromeOptions()
        # 设置中文
        options.add_argument('lang=zh_CN.UTF-8')
        # 设置无图加载 1 允许所有图片; 2 阻止所有图片; 3 阻止第三方服务器图片
        prefs = {
            'profile.default_content_setting_values': {'images': 1}
        }
        options.add_experimental_option('prefs', prefs)
        # 设置无头浏览器
        # options.add_argument('--headless')
        self.browser = webdriver.Chrome(chrome_options=options, executable_path="F:/ChromeDriver/chromedriver.exe")

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler)
        o.set_browser(crawler.settings)
        return o

    def set_browser(self, settings):
        settings.set('seleniumBrowser', self.browser)
