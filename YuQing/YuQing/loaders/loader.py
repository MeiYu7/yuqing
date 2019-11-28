from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst,MapCompose,Join,Identity


class NewsItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class NewsCommentsItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

    # try_name_in = MapCompose()
    # try_name_out = Join()

