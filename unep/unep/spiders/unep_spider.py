import scrapy
from unep.items import UnepItem
from copy import deepcopy


class UnepSpiderSpider(scrapy.Spider):
    name = 'unep_spider'
    allowed_domains = ['unep.org']
    start_urls = ['https://www.unep.org/resources?f%5B0%5D=category%3A451']

    def __init__(self):
        self.current_page = 0

    def parse(self, response):
        item = UnepItem()
        news_items = response.xpath('//div[@class="result_items"]//div[@class="views-row"]')
        for single_news in news_items:
            item['title'] = single_news.xpath('.//div[@class="result_item_title"]//a//text()').extract_first()
            article_url = response.urljoin(single_news.xpath('.//div[@class="result_item_title"]//a/@href').extract_first())
            yield scrapy.Request(url=article_url, meta={'item': deepcopy(item)}, callback=self.parse_article)

        if self.current_page < 2:
            yield scrapy.Request(url=self.get_next(), callback=self.parse)

    def get_next(self):
        self.current_page += 1
        return 'https://www.unep.org/resources?f%5B0%5D=category%3A451&keywords=&page=' + str(self.current_page)

    def parse_article(self, response):
        item = response.meta['item']
        item['article'] = ''.join(response.xpath('//div[@class="para_content_text"]/div/p//text()').extract())

        return item
