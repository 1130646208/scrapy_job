import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time

oecd_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""


oecd_article_script = """
function main(splash, args)
    splash.resource_timeout = 90
    splash.images_enabled = false
    splash:go(args.url)
    return {
    html=splash:html(),
    url=splash:url()
    }
end
"""

class OecdNewsSpider(scrapy.Spider):
    name = 'oecd_news'
    allowed_domains = ['oecd.org']
    start_urls = ['https://www.oecd.org/newsroom/publicationsdocuments/bydate/{}']
    page_limit = 2
    # 共222页
    def start_requests(self):
        for page in range(1, self.page_limit+1):
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': unitar_homepage_script, 'timeout': 90})
            if page == 1:
                yield SplashRequest(self.start_urls[0].format(''), callback=self.homepage_parse, endpoint='execute',
                                    args={'lua_source': oecd_homepage_script, 'timeout': 90})
            else:
                yield SplashRequest(self.start_urls[0].format(page), callback=self.homepage_parse, endpoint='execute',
                                    args={'lua_source': oecd_homepage_script, 'timeout': 90})

    def homepage_parse(self, response):

        news_list = response.xpath('//div[@class="span-19 last"]//li[@class="row item"]')
        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'Organization for Economic Co-operation and Development'
            item['category'] = 'Publications & Documents'
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//div[@class="block"]//h4//a//text()').extract_first().strip()
            item['issueAgency'] = 'OECD'
            issueTime_raw = news.xpath('.//div[@class="left"]//p[@class="date"]//text()').extract_first()
            item['issueTime'] = ' '.join(issueTime_raw.split('-'))
            article_detail_url = news.xpath('.//div[@class="block"]//h4//a/@href').extract_first()
            item['url'] = response.urljoin(article_detail_url)
            item['abstract'] = news.xpath('.//div[@class="block"]/p[@class="content"]/text()').extract_first().strip()
            # yield item
            yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': oecd_article_script, 'timeout': 90},
                                meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_paragraphs = response.xpath('//div[@id="webEditContent"]//p')
        article = []
        for paragraph in article_paragraphs:
            p_text = paragraph.xpath('.//text()').extract()
            p = []
            for t in p_text:
                p_clean = t.replace('\r', '').replace('\n', '').replace('\xa0', '')
                if p_clean:
                    p.append(p_clean)
            temp = ''.join(p)
            article.append(temp + '\n')
        item['detail'] = ''.join(article).lstrip('\n')
        yield item
