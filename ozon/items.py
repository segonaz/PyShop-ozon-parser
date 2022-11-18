import scrapy


class OzonItem(scrapy.Item):
    os_name = scrapy.Field()
    os_version = scrapy.Field()
