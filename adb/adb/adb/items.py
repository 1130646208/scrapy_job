# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapysplashnewsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    table = 'news'
    title = scrapy.Field()#
    organization = scrapy.Field()#
    issueAgency = scrapy.Field()#
    issueTime = scrapy.Field()#
    category = scrapy.Field()#
    url = scrapy.Field()#
    crawlTime = scrapy.Field()#
    abstract = scrapy.Field()
    detail = scrapy.Field()#
