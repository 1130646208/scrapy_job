import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time
from copy import deepcopy

unicef_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""


class YouthenvoyNewsSpider(scrapy.Spider):
    name = 'youthenvoy_news'
    allowed_domains = ['un.org']
    start_urls = ['https://www.un.org/youthenvoy/category/news/page/0/']
    page_num = 1
    page_limit = 5

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': unicef_homepage_script, 'timeout': 90})

    def homepage_parse(self, response):
        item = ScrapysplashnewsItem()
        news_list = response.xpath('//article')

        for news in news_list:
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//h2//text()').extract_first()
            item['issueAgency'] = 'Secretary-General’s Envoy on Youth'
            raw_issueTime_day = news.xpath('.//span[@class="fusion-date"]//text()').extract_first()
            raw_issueTime_month_year = news.xpath('.//span[@class="fusion-month-year"]//text()').extract_first()

            item['issueTime'] = self.parse_date_time(raw_issueTime_day, raw_issueTime_month_year)

            article_detail_url = news.xpath('.//h2/a/@href').extract_first()
            item['url'] = article_detail_url
            item['abstract'] = news.xpath('.//div[@class="fusion-post-content-container"]/p/text()').extract_first().strip(' ')
            # yield item
            yield SplashRequest(article_detail_url, callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': unicef_homepage_script, 'timeout': 90},
                                meta={'item': deepcopy(item)})

        if response.status != 404 and self.page_num < self.page_limit:
            self.page_num += 1
            new_url = 'https://www.un.org/youthenvoy/category/news/page/{}/'.format(self.page_num)
            yield SplashRequest(new_url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': unicef_homepage_script, 'timeout': 90},
                                meta={'item': deepcopy(item)})

        # #                                       这里更改要爬取的页数↓
        # if next_page_query and next_page_query.split('=')[1] < '5':
        #     base_url = response.request.url.split('?')[0]
        #     yield scrapy.Request(url=base_url + next_page_query, callback=self.parse)

    def parse_date_time(self, day, month_year):
        _day = day.strip('\n').strip('\t')
        _month = month_year.strip('\n').strip('\t').split(',')[0]
        _year = month_year.strip('\n').strip('\t').split(',')[1].strip(' ')
        return ' '.join([_day, self.parse_month(_month), _year])

    def parse_article_detail(self, response):
        article_paragraphs = response.xpath('//div[@class="et_pb_text_inner"]//p/text()').extract()
        article = []
        if not article_paragraphs:

            article_paragraphs = response.xpath('//div[@class="post-content"]//p/text()').extract()

        for paragraph in article_paragraphs:
            article.append(''.join(paragraph) + '\n')
        item = response.meta['item']
        item['detail'] = ''.join(article)
        return item

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
