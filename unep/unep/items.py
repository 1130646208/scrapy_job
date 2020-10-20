# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UnepItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # item['title'] = response.meta['title']
    # item['organization'] = 'United Nations'
    # item['issueAgency'] = 'Department of Economic and Social Affairs Sustainable Development'
    # item['url'] = response.data['url']
    # item['crawlTime'] = str(datetime.datetime.now().date())
    title = scrapy.Field()
    date = scrapy.Field()
    article = scrapy.Field()
    news_type = scrapy.Field()
