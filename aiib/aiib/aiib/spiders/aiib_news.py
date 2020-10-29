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


class AiibNewsSpider(scrapy.Spider):
    name = 'aiib_news'
    allowed_domains = ['aiib.org']
    start_urls = ['https://www.aiib.org/en/news-events/media-center/news/index.html']
    # 此网站所有内容全在一个页面(html控制显示隐藏.)

    def start_requests(self):

        for url in self.start_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': homepage_script, 'timeout': 90})
            # yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):
        years = [2020, 2019]
        # years = [2020, 2019, 2018, 2017, 2016, 2015]
        for year in years:
            articles = response.xpath('//div[contains(@class, "news-list page-{}")]/div/a[not(contains(@class,*))]'.format(year))
            for article in articles:
                item = ScrapysplashnewsItem()
                item['organization'] = 'Asian Infrastructure Investment Bank'
                item['category'] = 'News of ' + str(year)
                item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
                item['title'] = article.xpath('.//div[contains(@class, "col-xs-12")]//h3/text()').extract_first()
                item['issueAgency'] = 'AIIB'
                issueTime_raw = article.xpath('.//div[contains(@class, "col-xs-12")]//p[@class="Rbt-MD text-14 grey"]/text()').extract_first()
                item['issueTime'] = issueTime_raw
                item['abstract'] = article.xpath('.//div[contains(@class, "col-xs-12")]//p[contains(@class,"copy-desc Rbts-RG text-15 grey Copy-Ellipsis")]/text()').extract_first()
                article_detail_url = article.xpath('./@href').extract_first()
                item['url'] = response.urljoin(article_detail_url)
                # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                #                     args={'lua_source': wto_homepage_script, 'timeout': 90},
                #                     meta={'item': deepcopy(item)})
                yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})
            # 并发太多,用splash可能不稳定
            # yield item

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_units = response.xpath('//div[@class="detail-article Rbts-LT text-18"]//p')

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
        item['detail'] = article_detail
        yield item
