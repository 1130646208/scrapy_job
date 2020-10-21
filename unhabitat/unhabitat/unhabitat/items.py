# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UnhabitatItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()#
    organization = scrapy.Field()#
    crawlTime = scrapy.Field()#
    detail = scrapy.Field()#
    issueTime = scrapy.Field()#
    abstract = scrapy.Field()
    _url = scrapy.Field()#
    issueAgency = scrapy.Field()#
    category = scrapy.Field()#

