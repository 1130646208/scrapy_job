import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time
from copy import deepcopy


unitar_homepage_script = """
    function main(splash, args)
        splash.resource_timeout = 90
        splash.images_enabled = false
        assert(splash:go(args.url))
        return splash:html()
    end
"""

class UnitarNewsSpider(scrapy.Spider):
    name = 'unitar_news'
    allowed_domains = ['unitar.org']

    # 这个网站就两页....
    start_urls = ['https://www.unitar.org/about/news-stories/press?title=&created_start=&created_end=&pillars=All&items_per_page=10&page=0',
                  'https://www.unitar.org/about/news-stories/press?title=&created_start=&created_end=&pillars=All&items_per_page=10&page=1']

    def start_requests(self):
        for url in self.start_urls:
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': unitar_homepage_script, 'timeout': 90})
            yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):

        news_list = response.xpath('//div[@class="item-new views-row"]')

        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//div[@class="views-field views-field-title"]/span/a/text()').extract_first()
            item['issueAgency'] = 'United Nations Institute for Training and Research'
            item['issueTime'] = news.xpath('.//div[@class="views-field views-field-created"]/span/text()').extract_first()

            article_detail_url = news.xpath('.//div[@class="views-field views-field-title"]/span/a/@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            item['abstract'] = news.xpath('.//div[@class="views-field views-field-field-summary"]/div/text()').extract_first()
            # yield item
            # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
            #                     args={'lua_source': unitar_homepage_script, 'timeout': 90},
            #                     meta={'item': deepcopy(item)})
            yield scrapy.Request(url=response.urljoin(article_detail_url), callback=self.parse_article_detail, meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_paragraphs = response.xpath('//div[@class="field--item"]//p')
        article = []
        # if not article_paragraphs:
        #     article_paragraphs = response.xpath('//div[@class="post-content"]//p/text()').extract()

        for paragraph in article_paragraphs:
            p_text = paragraph.xpath('.//text()').extract()
            p = []
            for t in p_text:
                p.append(t.replace('\n', '').strip())
            article.append(''.join(p) + '\n')

        item['detail'] = ''.join(article)
        yield item


