import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
import datetime
import time


wto_homepage_script = """
    function main(splash, args)
        splash.js_enabled = true
        splash.resource_timeout = 450
        splash.images_enabled = false
        assert(splash:go(args.url))
        return {html=splash:html(),
        url=splash:url()
        }
    end
"""


class WtoNewsSpider(scrapy.Spider):
    name = 'wto_news'
    allowed_domains = ['wto.org']
    start_urls = ['https://www.wto.org/english/news_e/news_e.htm']

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': wto_homepage_script, 'timeout': 450})
            # yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):
        news_list = response.xpath('//div[@class="centerCol"]//div[@class="row"]')
        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//h3//text()').extract_first()
            item['issueAgency'] = 'World Trade Organization'
            item['issueTime'] = news.xpath('.//time//text()').extract_first()
            article_detail_url = news.xpath('.//ul//li/a/@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            abstract_raw = news.xpath('.//p//text()').extract()
            item['abstract'] = ''.join([i.replace('\n', '').strip() for i in abstract_raw])

            yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': wto_homepage_script, 'timeout': 90},
                                meta={'item': item})
            # yield item
            # yield scrapy.Request(item['url'], callback=self.homepage_parse, meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_paragraphs = response.xpath('//div[@id="mainContent"]//p')
        article = []

        for paragraph in article_paragraphs:
            p = []
            for p_text in paragraph.xpath('.//text()').extract():
                p.append(p_text.replace('\n', '').strip())
            article.append(''.join(p) + '\n')

        item['detail'] = ''.join(article)
        yield item
