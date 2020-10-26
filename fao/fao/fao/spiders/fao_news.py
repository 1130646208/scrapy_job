import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
from copy import deepcopy
import datetime
import time
import re


fao_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""


class FaoNewsSpider(scrapy.Spider):
    name = 'fao_news'
    allowed_domains = ['fao.org']
    start_urls = ['http://www.fao.org/news/archive/news-by-date/2020/en/?page={}']
    # 本网站目前只有16页
    page_limit = 3

    def start_requests(self):
        page_urls = []
        for i in range(1, self.page_limit+1):
            page_urls.append(self.start_urls[0].format(i))
            print(page_urls)

        for url in page_urls:
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': fao_homepage_script, 'timeout': 90})
            yield scrapy.Request(url, callback=self.homepage_parse)

    def homepage_parse(self, response):
        item = ScrapysplashnewsItem()
        news_list = response.xpath('//div[@class="news-list"]/div[contains(@class, tx-dynalist-pi1-recordlist)]')
        for news in news_list:
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//div[@class="list-title"]//a//text()').extract_first()
            item['issueAgency'] = 'Food and Agriculture Organization of the United Nations'
            raw_issueTime = news.xpath('.//div[@class="list-date"]//text()').extract_first()

            item['issueTime'] = self.parse_date_time(raw_issueTime)

            article_detail_url = response.urljoin(news.xpath('.//div[@class="list-title"]/a/@href').extract_first())
            item['url'] = article_detail_url
            item['abstract'] = news.xpath('.//div[@class="list-subtitle"]/text()').extract_first()

            yield scrapy.Request(article_detail_url, callback=self.parse_article_detail, meta={'item': deepcopy(item)})

    def parse_article_detail(self, response):
        article_paragraphs = response.xpath('//div[@class="news-list"]//text()').extract()
        article = []

        for paragraph in article_paragraphs:
            article.append(''.join(paragraph))
        item = response.meta['item']
        item['detail'] = ''.join(article)
        yield item

    def parse_date_time(self, date_raw):
        day_month_year_list = date_raw.split('-')
        _ctime = datetime.datetime(int(day_month_year_list[2]), int(day_month_year_list[1]), int(day_month_year_list[0])).ctime()
        _ctime_list = re.split(r'\s+', _ctime)
        return ' '.join([_ctime_list[2], self.parse_month(_ctime_list[1]), _ctime_list[4]])

    def parse_month(self, month):
        mapping = {
            'Jan': 'January',
            'Feb': 'February',
            'Mar': 'March',
            'Apr': 'April',
            'May': 'May',
            'Jun': 'June',
            'Jul': 'July',
            'Aug': 'August',
            'Sep': 'September',
            'Oct': 'October',
            'Nov': 'November',
            'Dec': 'December',
        }
        return mapping[month]
