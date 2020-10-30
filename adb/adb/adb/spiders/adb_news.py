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

adb_article_script = """
function main(splash, args)
    splash.resource_timeout = 15
    splash.images_enabled = false
    splash:go(args.url)
    return {html=splash:html(),
    }
end
"""


class AdbNewsSpider(scrapy.Spider):
    name = 'adb_news'
    allowed_domains = ['adb.org']
    start_urls = ['https://www.adb.org/news/releases', 'https://www.adb.org/news/country-offices', 'https://www.adb.org/news/articles']
    page_urls = []
    # 爬取的时候改 which, 0对应start_requests第一个网址,1对应start_requests第二个网址...
    # 然后将page_limit改到需要的大小
    which = 2
    page_limit1 = 3  # 最大479
    page_limit2 = 3  # 最大244
    page_limit3 = 3  # 最大55
    page_limit = [page_limit1, page_limit2, page_limit3]
    def start_requests(self, which_to_crawl=which):
        self.page_urls.append(self.start_urls[which_to_crawl])
        for i in range(1, self.page_limit[which_to_crawl]+1):
            self.page_urls.append(self.start_urls[which_to_crawl] + '?page={}'.format(i))
        for url in self.page_urls:
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': homepage_script, 'timeout': 90})
            # yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):

        articles = response.xpath('//div[@class="views-list"]/ul/li')
        for article in articles:
            item = ScrapysplashnewsItem()
            item['organization'] = 'Asian Development Bank'
            item['category'] = response.data['url'].split('/')[-1].split('?')[0]
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = article.xpath('.//h3/text()').extract_first()
            item['issueAgency'] = 'ADB'
            issueTime_raw = article.xpath('.//span[@class="date-display-single"]/text()').extract_first()
            item['issueTime'] = self.parse_issueTime(issueTime_raw)

            if self.which == 2:
                item['abstract'] = article.xpath('.//div/text()').extract_first()
                article_detail_url = article.xpath('./a/@href').extract_first()
                item['url'] = response.urljoin(article_detail_url)
            else:
                item['abstract'] = article.xpath('.//div[2]/div/text()').extract_first()
                article_detail_url = article.xpath('.//span/a/@href').extract_first()
                item['url'] = response.urljoin(article_detail_url)
            yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
                                args={'lua_source': adb_article_script, 'timeout': 90},
                                meta={'item': item})
            # yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_units = response.xpath('//article//p')

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

    def parse_issueTime(self, issueTime_raw):
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
        year = issueTime_raw.split(' ')[2]
        month = issueTime_raw.split(' ')[1].capitalize()
        day = issueTime_raw.split(' ')[0]

        if month in mapping.keys():
            month = mapping[month]
        return ' '.join([day, month, year])
