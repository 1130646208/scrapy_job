import scrapy
from scrapy_splash import SplashRequest

from ..items import ScrapysplashnewsItem
import datetime
import time
import json
from lxml import etree


class UnescapNewsSpider(scrapy.Spider):
    name = 'unescap_news'
    allowed_domains = ['unescap.org']
    start_urls = ['https://www.unescap.org/views/ajax?_wrapper_format=drupal_ajax']
    # 暂时不清楚共多少页,可以设置page_limit大一些, 程序会自动停止
    page = 1
    page_limit = 3
    form_data = {
        'page': '1',
        'view_name': 'news_view_page_solr',
        'view_display_id': 'page_1',
        'view_path': '/news',
        'view_base_path': 'news',
        'view_dom_id': '0ce23155dc390f7b095c648cf60a7ba6ba547b645cd9b81a7a43d464f5140d04',
        'pager_element': '0',
        '_drupal_ajax': '1',
        'ajax_page_state[theme]': 'escap2020',
    }

    def start_requests(self):
        yield scrapy.FormRequest(self.start_urls[0], formdata=self.form_data, callback=self.homepage_parse)

    def homepage_parse(self, response):
        d = json.loads(response.text)
        html = d[-1].get('data')
        html = etree.HTML(html)
        news_list = html.xpath('//div[@class="item-list"]//ul//li')
        # print(etree.tostring(news_list[0], pretty_print=True))
        for news in news_list:
            item = ScrapysplashnewsItem()
            item['organization'] = 'United Nations'
            item['category'] = 'news'
            item['crawlTime'] = datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')
            title_raw = news.xpath('.//h5[@class="card-title"]/text()')
            item['title'] = title_raw.pop().strip().strip('\n')
            item['abstract'] = news.xpath('.//div[@class="sub-text"]//text()')[0].replace('\r', '').replace('\n', '').replace('&nbsp', ' ')
            item['issueAgency'] = 'Economic and Social Commission for Asia and the Pacific'
            issueTime_raw = news.xpath('.//div[@class="date"]//text()')
            item['issueTime'] = self.parse_issueTime_raw(issueTime_raw)
            article_detail_url = news.xpath('.//a[@aria-label="Title link"]/@href')
            # print(title_raw, issueTime_raw, article_detail_url)
            item['url'] = response.urljoin(article_detail_url[0])
            # yield SplashRequest(item['url'], callback=self.parse_article_detail, endpoint='execute',
            #                     args={'lua_source': wto_homepage_script, 'timeout': 90},
            #                     meta={'item': deepcopy(item)})
            yield scrapy.Request(url=item['url'], callback=self.parse_article_detail, meta={'item': item})
            # yield item

        if response.status == 200 and self.page <= self.page_limit:
            self.page += 1
            self.form_data['page'] = str(self.page)
            yield scrapy.FormRequest(self.start_urls[0], formdata=self.form_data, callback=self.homepage_parse)

    def parse_article_detail(self, response):
        item = response.meta['item']
        article_units = response.xpath('//div[@class="article-content-wrapper"]//p')
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

    def parse_issueTime_raw(self, issueTime_raw):
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

        date_list = []
        for i in issueTime_raw:
            clean = i.strip().replace('\n', '')
            if clean == '':
                continue
            else:
                date_list.append(clean)

        return ' '.join([date_list[0], mapping[date_list[1]], date_list[2]])
