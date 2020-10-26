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


class IfadNewsSpider(scrapy.Spider):
    name = 'ifad_news'
    allowed_domains = ['ifad.org']
    start_urls = ['https://www.ifad.org/en/web/latest/news?mode=search&page=1']
    page_limit = 3  # 共113页

    def start_requests(self):
        page_urls = []
        for i in range(1, self.page_limit+1):
            page_urls.append('https://www.ifad.org/en/web/latest/news?mode=search&page={}'.format(i))
        for url in page_urls:
            # yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
            #                     args={'lua_source': homepage_script, 'timeout': 90})
            yield scrapy.Request(url=url, callback=self.homepage_parse)

    def homepage_parse(self, response):

        news_list = response.xpath('//div[@class="span8 offset2"]//div[@class="row-fluid"]//div[@class="row-fluid abstract-row"]')

        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = ''
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = news.xpath('.//p[@class="event-title ellipsis"]//text()').extract()[1].strip()
            item['issueAgency'] = 'International Fund for Agricultural Development'
            issueTime_raw = news.xpath('.//div[@class="event-date"]//text()').extract()
            item['issueTime'] = self.parse_issueTime_raw(issueTime_raw)
            article_detail_url = news.xpath('.//div[@class="event-row-categories"]//a[contains(text(), "English")]/@href').extract_first()
            if not article_detail_url:
                article_detail_url = news.xpath('.//div[@class="event-row-categories"]//a[last()]/@href').extract_first()

            item['url'] = response.urljoin(article_detail_url)
            # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
            #                     args={'lua_source': wto_homepage_script, 'timeout': 90},
            #                     meta={'item': deepcopy(item)})
            yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})
            # yield item

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_paragraphs = response.xpath('//div[@class="main-content generic-container row-fluid"]//p')
        article = []
        for paragraph in article_paragraphs:
            p_text = paragraph.xpath('.//text()').extract()
            p = []
            for t in p_text:
                p.append(t.replace('\n', '').strip())
            article.append(''.join(p) + '\n')
        item['detail'] = ''.join(article)

        item['abstract'] = ''.join(article)[0:150] + '...'
        yield item

    def parse_issueTime_raw(self, issueTime_raw):

        day = issueTime_raw[1]
        month = issueTime_raw[3].capitalize()
        year = '2020'
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

        return ' '.join([day, mapping[month], year])
