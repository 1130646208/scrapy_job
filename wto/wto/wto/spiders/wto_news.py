import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time
from copy import deepcopy


wto_homepage_script = """
    function main(splash, args)
        splash.js_enabled = true
        splash.resource_timeout = 90
        splash.images_enabled = false
        assert(splash:go(args.url))
        return splash:html()
    end
"""

class WtoNewsSpider(scrapy.Spider):
    name = 'wto_news'
    allowed_domains = ['wto.org']
    start_urls = ['https://www.wto.org/english/news_e/news20_e/news20_e.htm']

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': wto_homepage_script, 'timeout': 90})

    def homepage_parse(self, response):
        item = ScrapysplashnewsItem()
        news_list = response.xpath('//div[@class="centerCol"]//div[@class="row"]')
        print('*********************', response.request.url)
        for news in news_list:
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//h3//text()').extract_first()
            item['issueAgency'] = 'World Trade Organization'
            item['issueTime'] = news.xpath('.//time//text()').extract_first()
            article_detail_url = news.xpath('.//ul//li//text()').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            item['abstract'] = news.xpath('.//p/text()').extract_first()
            yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': wto_homepage_script, 'timeout': 90},
                                meta={'item': deepcopy(item)})


    def parse_article_detail(self, response):
        article_paragraphs = response.xpath('//div[@id="mainContent"]//p//text()').extract()
        article = []
        # if not article_paragraphs:
        #     article_paragraphs = response.xpath('//div[@class="post-content"]//p/text()').extract()

        for paragraph in article_paragraphs:
            if not paragraph.replace('\n', '').replace(' ', '') == '':
                article.append(''.join(paragraph) + '\n')
        item = response.meta['item']
        item['detail'] = ''.join(article)
        yield item
