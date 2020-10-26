import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
import datetime
import time

homepage_script = """
function main(splash, args)
    splash.resource_timeout = 10
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""

class WipoNewsSpider(scrapy.Spider):
    name = 'wipo_news'
    allowed_domains = ['wipo.int']
    start_urls = ['https://www.wipo.int/portal/en/news/']

    def start_requests(self):
        for i in range(1):
            # yield SplashRequest(self.start_urls[0], callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': homepage_script, 'timeout': 90})
            yield scrapy.Request(url=self.start_urls[0], callback=self.homepage_parse)

    def homepage_parse(self, response):
        news = response.xpath('//div[@class="listings listings--news"]//article[@class="listing listing--news"]')
        for single_news in news:
            item = ScrapysplashnewsItem()
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['organization'] = 'United Nations'
            item['issueAgency'] = 'World Intellectual Property Organization'
            item['title'] = single_news.xpath('.//h3[@class="listing__title"]/a/text()').extract_first()
            issueTime_raw = single_news.xpath('.//p[@class="secondary"]/time/text()').extract_first()
            item['issueTime'] = self.parse_issueTime_raw(issueTime_raw)
            detail_url = response.urljoin(single_news.xpath('.//h3[@class="listing__title"]/a/@href').extract_first())
            item['url'] = detail_url

            # yield SplashRequest(detail_url, callback=self.abstract_parse, endpoint='execute', args={'lua_source': homepage_script, 'timeout': 90},
            #                     meta={'item': item})
            yield item
            # yield scrapy.Request(url=detail_url, callback=self.abstract_parse, meta={'item': item})

    def abstract_parse(self, response):

        if response.status == 200:
            item = response.meta['item']

            detail_url = response.xpath('//div[@class="content content--article"]//ul//li/a/@href').extract_first()

            # 详情页是摘要和详情连接
            if detail_url:
                abstract_raw = response.xpath('//div[@class="content content--article"]//p//text()').extract()
                abstract = []
                for i in abstract_raw:
                    abstract.append(i.strip('\n'))
                item['abstract'] = ''.join(abstract)[0:100]
                # yield SplashRequest(detail_url, callback=self.abstract_parse, endpoint='execute', args={'lua_source': homepage_script, 'timeout': 90},
                #                     meta={'item': item})
                # yield scrapy.Request(url=detail_url, callback=self.article_parse, meta={'item': item})
                yield item

            # 详情页是文章详情
            else:
                raw = response.xpath('//div[@class="content content--article"]//p[@class="lead"]//text()').extract_first()
                item['abstract'] = raw[0:100]
                # item['detail'] = ''.join(detail_raw)
                # for detail in detail_raw:
                #     ''.join()
                yield item
        else:
            # 重定向情况
            pass

    def article_parse(self, response):
        item = response.meta['item']
        article_raw = response.xpath('//div[@class="content content--article"]//text()').extract()
        article = []
        for i in article_raw:
            article.append(i)
        item['detail'] = article
        yield item

    def parse_issueTime_raw(self, issueTime_raw):

        temp_list = issueTime_raw.split(' ')

        _month = temp_list[0]
        _day = temp_list[1].strip(',')
        _year = temp_list[2]
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
        return ' '.join([_day, mapping[_month], _year])