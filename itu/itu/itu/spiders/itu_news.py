import scrapy
from ..items import ScrapysplashnewsItem
from scrapy_splash import SplashRequest
import datetime
import time
# 以下代码在splash网页端直接执行可以成功翻页
next_page_lua = """
    function main(splash, args)
    splash:html = args.html
    splash:evaljs("__doPostBack('ctl00$SPWebPartManager1$g_b1bc0681_86db_42ff_aebf_c5303a4b2ae1$lstPressReleases$DataPager1$ctl02$ctl00','')")
    splash:wait(10)
    return splash:html()
end
"""


class ItuNewsSpider(scrapy.Spider):
    name = 'itu_news'
    allowed_domains = ['itu.int']
    start_urls = ['https://www.itu.int/zh/mediacentre/pages/all-pr.aspx']

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.homepage_parse)

    def homepage_parse(self, response):

        detail_list = response.xpath(
            '//div[@id="ctl00_SPWebPartManager1_g_b1bc0681_86db_42ff_aebf_c5303a4b2ae1"]//a[contains(@href, "https")]/@href').extract()
        title_list = response.xpath(
            '//div[@id="ctl00_SPWebPartManager1_g_b1bc0681_86db_42ff_aebf_c5303a4b2ae1"]//a[contains(@href, "https")]/text()').extract()
        date_list = response.xpath(
            '//div[@id="ctl00_SPWebPartManager1_g_b1bc0681_86db_42ff_aebf_c5303a4b2ae1"]//strong/text()').extract()
        for i in range(len(title_list)):
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['issueAgency'] = 'International Telecommunication Union'
            item['category'] = '新闻稿、公报和面向媒体的新闻提要'
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            item['title'] = title_list.pop(0).strip()
            issueTime_raw = date_list.pop(0).strip()
            item['issueTime'] = self.parse_date_time(issueTime_raw)
            item['url'] = detail_list.pop(0)
            yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})

        yield SplashRequest(self.start_urls[0], callback=self.homepage_parse, endpoint='execute',
                            args={'lua_source': next_page_lua, 'timeout': 90})

    def parse_article_detail(self, response):
        item = response.meta['item']
        if response.xpath('//h1[contains(text(),"新闻稿") or contains(text(),"媒体公告") or contains(text(),"成员公报")]'):
            article_paragraphs = response.xpath(
                '//div[@id="ctl00_PlaceHolderMain_TopHeaderDisplayPanel_ctl01__ControlWrapper_RichHtmlField"]//div')
            article = []
            for paragraph in article_paragraphs:
                p_text = paragraph.xpath('.//text()').extract()
                p = []
                for t in p_text:
                    p_clean = t.replace('\u200b', '').replace('\xa0', '').replace('\r', '').replace('\n', '').replace(
                        ' ', '')
                    if p_clean:
                        p.append(p_clean)
                article.append(''.join(p) + '\n')
            item['detail'] = ''.join(article).lstrip('\n').replace('\n\n', '\n')
            item['abstract'] = item['detail'][0:100] + '...'
        else:
            article = []
            article_paragraphs = response.xpath(
                '//div[@id="ctl00_PlaceHolderMain_TopHeaderDisplayPanel_ctl01__ControlWrapper_RichHtmlField"]//p')
            for paragraph in article_paragraphs:
                p_text = paragraph.xpath('.//text()').extract()
                p = []
                for t in p_text:
                    p.append(t.strip('\n').replace('\n', '').strip())
                article.append(''.join(p) + '\n')
            item['detail'] = ''.join(article)
            item['abstract'] = item['detail'][0:100] + '...'

        yield item

    def parse_date_time(self, date_raw):
        day_month_year_list = date_raw.split(' ')
        mapping = {
            '一月': 'January',
            '二月': 'February',
            '三月': 'March',
            '四月': 'April',
            '五月': 'May',
            '六月': 'June',
            '七月': 'July',
            '八月': 'August',
            '九月': 'September',
            '十月': 'October',
            '十一月': 'November',
            '十二月': 'December',
        }
        return ' '.join([day_month_year_list[0], mapping[day_month_year_list[1]], day_month_year_list[2]])
