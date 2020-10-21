import scrapy
from ..items import UnhabitatItem
from copy import deepcopy
import datetime
import time


class UnhabitatSpiderSpider(scrapy.Spider):
    name = 'unhabitat_spider'
    allowed_domains = ['unhabitat.org']
    start_urls = ['https://unhabitat.org/news-and-stories-archive?page=0']

    def parse(self, response):
        item = UnhabitatItem()
        news_list = response.xpath('//li[@class="list-group-item"]')
        next_page_query = response.xpath('//li[@class="pager__item--next"]/a/@href').extract_first()
        for news in news_list:
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('./h4/a/text()').extract_first()
            item['issueAgency'] = 'United Nations Human Settlements Programme'
            raw_issueTime = news.xpath('./p[2]/text()').extract_first()
            item['issueTime'] = self.parse_date_time(raw_issueTime)
            article_detail_url = response.urljoin(news.xpath('./h4/a/@href').extract_first())
            yield scrapy.Request(url=article_detail_url, meta={'item': deepcopy(item)}, callback=self.parse_article_detail)

        #                                       这里更改要爬取的页数↓
        if next_page_query and next_page_query.split('=')[1] < '5':
            base_url = response.request.url.split('?')[0]
            yield scrapy.Request(url=base_url+next_page_query, callback=self.parse)

    def parse_date_time(self, date_time: str):
        temp = date_time.strip(' ').split(' ')
        return ' '.join([temp[1], temp[2].rstrip(','), temp[3]])

    def parse_article_detail(self, response):
        article_paragraphs = response.xpath('//div[@class="field__item"]//div[@class="container"]//p')
        article = []
        for paragraph in article_paragraphs:
            article.append(''.join(paragraph.xpath('.//text()').extract()) + '\n')

        item = response.meta['item']
        item['detail'] = ''.join(article)
        item['_url'] = response.request.url
        item['abstract'] = item['detail'][0:100] + '...'

        return item
