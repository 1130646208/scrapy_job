import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
import datetime
import time

homepage_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    assert(splash:go(args.url))
    return {html=splash:html(),
    url=splash:url()
    }
end
"""

article_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    splash:go(args.url)
    return {html=splash:html(),
    }
end
"""


class UncitralNewsSpider(scrapy.Spider):
    name = 'uncitral_news'
    allowed_domains = ['uncitral.un.org']
    start_urls = ['https://uncitral.un.org/en/gateway/meetings/events']
    # 本网站只有一页

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': homepage_script, 'timeout': 90})
            # yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):
        articles = response.xpath('//div[@class="view-content"]//div[contains(@class,"views-row")]')
        index = 0
        for article in articles:
            index += 1
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            if index <= 16:
                item['category'] = 'Events and Colloquial'
            else:
                item['category'] = 'New Articles'
            item['issueTime'] = ''.join(article.xpath('.//div[@class="field-content"]/span[contains(@class,"date-display")]//text()').extract())
            if not item['issueTime']:
                item['issueTime'] = article.xpath('.//span[@class="field-content"]//text()').extract_first()
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = article.xpath('.//h3/a/text()').extract_first()
            item['issueAgency'] = 'Industrial Development Organization'
            abstract_raw = article.xpath('.//div[@class="field-content"]/p//text()').extract()
            item['abstract'] = self.parse_abstract(abstract_raw)
            article_detail_url = article.xpath('.//h3/a/@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            # yield item
            yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': article_script, 'timeout': 90},
                                meta={'item': item})
            # yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_units = response.xpath('//div[@class="field-item even"]//p')

        article_detail = ''
        for article_unit in article_units:
            article_unit_parts = article_unit.xpath('.//text()').extract()
            if ''.join(article_unit_parts).strip() == '':
                continue
            for article_unit_part in article_unit_parts:
                sentence = article_unit_part.strip()
                if sentence:
                    article_detail += sentence + ' '
            article_detail += '\n'
        item['detail'] = article_detail.replace('\xa0', '')
        yield item

    def parse_abstract(self, abstract_raw):
        p = []
        for text in abstract_raw:
            p.append(text)
        return ''.join(p).strip('\n').replace('\xa0', '')
