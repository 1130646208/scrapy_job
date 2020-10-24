import scrapy
from ..items import ScrapysplashnewsItem
import datetime
import time


class WmoNewsSpider(scrapy.Spider):
    name = 'wmo_news'
    allowed_domains = ['public.wmo.int']
    page_limit = 5
    start_urls = ['https://public.wmo.int/en/media/news?page=0']
    page_num = 0


    def start_requests(self):
        # page_urls = []
        # for i in range(1, self.page_limit + 1):
        #     page_urls.append(self.start_urls[0].format(i))
        #     print(page_urls)

        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.homepage_parse)

    def homepage_parse(self, response):

        news_list = response.xpath('//div[@class="view-content"]//div[contains(@class, "views-row views-row-")]')

        # if response.status == 200 and self.current_page < self.page_limit:
        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//div[@class="pane-content"]/h2/a/text()').extract_first()
            item['issueAgency'] = 'World Meteorological Organization'
            item['abstract'] = news.xpath('.//div[@class="field-body"]/p/text()').extract_first()
            item['issueTime'] = news.xpath('.//span[@class="date-display-single"]//text()').extract_first()
            article_detail_url = response.urljoin(news.xpath('.//div[@class="pane-content"]/h2/a/@href').extract_first())
            item['url'] = article_detail_url
            yield scrapy.Request(url=article_detail_url, meta={'item': item}, callback=self.parse_article_detail)

        if response.status == 200 and self.page_num < self.page_limit:
            self.page_num += 1
            print(self.page_num, '******************************')
            next_page_url = 'https://public.wmo.int/en/media/news?page={}'.format(self.page_num)
            yield scrapy.Request(url=next_page_url, callback=self.homepage_parse)



    def parse_article_detail(self, response):
        article_paragraphs = response.xpath('//div[@class="pane-content"]//div[@class="field-body"]//text()').extract()
        article = []

        for paragraph in article_paragraphs:
            article.append(''.join(paragraph))

        item = response.meta['item']
        item['detail'] = ''.join(article)

        return item

