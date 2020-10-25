import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time

homepage_script = """
    function main(splash, args)
        splash.js_enabled = true
        splash.resource_timeout = 90
        splash.images_enabled = false
        assert(splash:go(args.url))
        return {html=splash:html(),
        url=splash:url()
        }
    end
"""


class UnwtoNewsSpider(scrapy.Spider):
    name = 'unwto_news'
    allowed_domains = ['unwto.org']
    start_urls = ['https://www.unwto.org/news?query=&page=0']
    page_limit = 5

    def start_requests(self):
        page_urls = []
        for i in range(self.page_limit):
            page_urls.append('https://www.unwto.org/news?query=&page={}'.format(i))
        for url in page_urls:
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': homepage_script, 'timeout': 90})
            yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):

        news_list = response.xpath('//div[@class="row"]//div[@class="col-sm-4"]')

        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//h2[@class="card__title"]/a/text()').extract_first()
            item['issueAgency'] = 'World Tourism Organization'
            issueTime_raw = news.xpath('.//span[@class="card__date"]/text()').extract_first()
            item['issueTime'] = self.parse_issueTime_raw(issueTime_raw)
            article_detail_url = news.xpath('.//h2[@class="card__title"]/a/@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
            #                     args={'lua_source': wto_homepage_script, 'timeout': 90},
            #                     meta={'item': deepcopy(item)})
            yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})
            # yield item

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_paragraphs = response.xpath('//div[@class="col-md-8 offset-md-1"]//p//text()').extract()
        abstract = response.xpath('//div[@class="col-md-8 offset-md-1"]//p[@class="p_brief"]/text()').extract_first()
        if abstract:
            article = []
            item['abstract'] = abstract.replace('\n', '').strip(' ')
            for paragraph in article_paragraphs:
                temp = paragraph.replace('\n', '')
                article.append(temp + '\n')
            item['detail'] = ''.join(article)
            yield item
        else:
            item['abstract'] = 'page removed...'
            item['detail'] = 'page removed...'

    def parse_issueTime_raw(self, issueTime_raw):

        day, month, year = issueTime_raw.split(' ')
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

        return ' '.join([day, mapping[month], year])
