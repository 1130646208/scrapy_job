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


class ApecNewsSpider(scrapy.Spider):
    name = 'apec_news'
    allowed_domains = ['apec.org']
    start_urls = ['https://www.apec.org/Press/News-Releases?Page=1']
    page_limit = 2

    def start_requests(self):
        page_urls = []
        for i in range(1, self.page_limit+1):
            page_urls.append('https://www.apec.org/Press/News-Releases?Page={}'.format(i))
        for url in page_urls:
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': homepage_script, 'timeout': 90})
            yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):
        articles1 = response.xpath('//div[@class="blog-listing__content"]//ul[@class="blog-listing__featured row"]//li//a')
        articles2 = response.xpath('//div[@class="blog-listing__content"]//ul[@class="blog-listing__static"]//li//a')
        articles3 = response.xpath('//div[@class="blog-listing__content"]//ul[@class="blog-listing__aside"]//li//a')
        articles = []
        articles.extend(articles1)
        articles.extend(articles2)
        articles.extend(articles3)

        for article in articles:
            item = ScrapysplashnewsItem()
            item['organization'] = 'Asia-Pacific Economic Cooperation'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = article.xpath('.//div[@class="news-snippet__details"]/h3/text()').extract_first()
            item['issueAgency'] = 'APEC'
            issueTime_raw = article.xpath('.//div[@class="news-snippet__details"]//p[@class="news-meta"]/text()').extract_first().split(',')[-1].strip()
            item['issueTime'] = issueTime_raw
            item['abstract'] = article.xpath('.//div[@class="news-snippet__details"]//p[@class="news-teaser"]/text()').extract_first()
            article_detail_url = article.xpath('.//@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
            #                     args={'lua_source': wto_homepage_script, 'timeout': 90},
            #                     meta={'item': deepcopy(item)})
            yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_units = response.xpath('//body/main[@id="mainContent"]/section/div/div/div//p')

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
