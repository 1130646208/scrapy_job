import scrapy
from scrapy_splash import SplashRequest
from ..items import ScrapysplashnewsItem
import datetime
import time
import re
from copy import deepcopy

unicef_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 10
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""

next_page_script = """
function main(splash, args)
    splash.resource_timeout = 90
    assert(splash:go(args.url))
    next = splash:select('[rel=next]')
    next:mouse_click()
    splash:wait(10)

    return splash:html()
end
"""


class UnicefNewsSpider(scrapy.Spider):
    name = 'unicef_news'
    allowed_domains = ['unicef.org']
    start_urls = ['https://www.unicef.org/reports']

    def start_requests(self):
        # for url in self.start_urls:
        #     yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
        #                         args={'lua_source': unicef_homepage_script, 'timeout': 90})

        for i in range(16):
            yield SplashRequest(self.start_urls[0], callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': next_page_script, 'timeout': 90})


    def homepage_parse(self, response):

        item = ScrapysplashnewsItem()
        news = response.xpath('//div[@class="list-content"]')
        for single_news in news:
            item['title'] = single_news.xpath('./a/@title').extract_first()
            item['abstract'] = single_news.xpath(
                './/div[@class="list-description grey_darker text-small"]/text()').extract_first().strip('\n').strip(
                ' ')
            issueTime_raw = single_news.xpath('.//span[@class="note list-date grey-dark"]').extract_first()
            # print(issueTime_raw, '*'*10)
            item['issueTime'] = self.parse_issueTime_raw(issueTime_raw)
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['organization'] = 'United Nations'
            item['issueAgency'] = 'United Nations International Children‘s Emergency Fund'
            item['abstract'] = single_news.xpath(
                './/div[@class="list-description grey_darker text-small"]/text()').extract_first().strip('\n').strip(
                ' ')

            detail_url = single_news.xpath('./a/@href').extract_first()
            item['url'] = response.urljoin(detail_url)
            yield SplashRequest(response.urljoin(detail_url), callback=self.article_parse, endpoint='execute',
                                args={'lua_source': unicef_homepage_script, 'timeout': 90},
                                meta={'item': deepcopy(item)})


    def article_parse(self, response):
        item = response.meta['item']
        detail_raw = response.xpath(
            '//div[contains(@class,"field paragraph field_component_text_content")]//p//text()').extract()
        if not detail_raw:
            detail_raw = response.xpath('//div[@class="file-block--text body1"]//p//text()').extract()

        item['detail'] = ''.join(detail_raw)
        item['category'] = response.xpath('//div[@class="related-topics"]//div[@class="container"]//text()').extract()[
            3]
        return item

    def parse_issueTime_raw(self, issueTime_raw):

        result = re.match(r'(?s).*(\d{2}/\d{2}/\d{4})', issueTime_raw, re.S).group(1).strip('\n').strip(' ')
        print(result)
        _datetime = result.split('/')
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
        if result:
            year = int(_datetime[2])
            month = int(_datetime[0])
            day = int(_datetime[1])
            temp = datetime.datetime(year, month, day).ctime().split(' ')
            temp2 = []
            for hh in temp:
                if hh:
                    temp2.append(hh)
            print(datetime.datetime(year, month, day).ctime())
            print(temp2, '*' * 20)
            return ' '.join([temp2[2], mapping[temp2[1]], temp2[4]])
        else:
            return ''
