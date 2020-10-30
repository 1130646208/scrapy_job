import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
import datetime
import time
import re

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


class UnidoNewsSpider(scrapy.Spider):
    name = 'unido_news'
    allowed_domains = ['unido.org']
    start_urls = ['https://www.unido.org/news']
    # 最大243
    page_limit = 3
    page_urls = []

    def start_requests(self):
        self.page_urls.append(self.start_urls[0])
        for i in range(1, self.page_limit + 1):
            self.page_urls.append(self.start_urls[0] + '?newsfilter=&page={}'.format(i))
        for url in self.page_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': homepage_script, 'timeout': 90})


    def homepage_parse(self, response):

        articles = response.xpath('//div[contains(@class, "view view-news")]//div[@class="views-row"]')
        for article in articles:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = 'News articles'
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = article.xpath('.//h3//text()').extract_first()
            item['issueAgency'] = 'Industrial Development Organization'
            abstract_raw = article.xpath('.//div[@class="row"]//div[@class="col-sm-9 text-align-justify margin_bottom--sms"]//text()').extract()
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
        article_units = response.xpath('//div[@class="content"]/div//p | //div[@class="content"]/div//ul//li')

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
        issueTime_raw = re.match(r'.*?(\d+\s\w+\s\d{4})', item['detail'])
        if issueTime_raw:
            item['issueTime'] = issueTime_raw.group(1)
        else:
            issueTime_raw = re.search(r'(\d+\s\w+)', item['detail'])
            item['issueTime'] = issueTime_raw.group(1) + ' 2020'
        yield item

    def parse_abstract(self, abstract_raw):
        p = []
        for text in abstract_raw:
            p.append(text.replace('\xa0', ' '))

        return ''.join(p).strip('\n')
