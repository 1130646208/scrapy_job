import scrapy


class IcjCijNewsSpider(scrapy.Spider):
    name = 'icj_cij_news'
    allowed_domains = ['icj-cij.org']
    start_urls = ['http://icj-cij.org/']

    def parse(self, response):
        pass
