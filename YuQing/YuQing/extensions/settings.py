class LoaderCustomSettings(object):

    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('CUSTOM_SETTINGS')
        # path = crawler.settings
        crawler.settings.setmodule(path)
        o = cls()
        return o