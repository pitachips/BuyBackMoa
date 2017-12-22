import re
import requests

from bs4 import BeautifulSoup
from math import ceil
from urllib.parse import quote, urlencode


yes24_base_url = 'http://www.yes24.co.kr/Mall/buyback/Search'
aladin_base_url = 'http://www.aladin.co.kr/shop/usedshop/wc2b_search.aspx'


class Crawl(object):
    def get_response(self, query, page):
        raise NotImplementedError

    def get_soup(self, response):
        """Make each page into BeautifulSoup object"""
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def get_result_count(self, soup):
        pass

    def check_num_pages(self, soup):
        result_count = self.get_result_count(soup)
        if result_count:
            result_count = int(re.search(r'\d+', result_count)[0])
            return ceil(result_count/self.items_per_page)
        else:
            return None   # 0건의 검색 결과

    def crawl(self, soup, query, cur_page, num_pages):
        raise NotImplementedError

    def __call__(self, query):
        cur_page = 1
        response = self.get_response(query, cur_page)
        soup = self.get_soup(response)
        num_pages = self.check_num_pages(soup)
        if num_pages is None:
            return None
        rs = self.crawl(soup, query, cur_page, num_pages)
        print("확인용")
        return rs


class Yes24Crawl(Crawl):
    def __init__(self):
        self.items_per_page = 20
        # self.link = ''

    def get_response(self, query, page):
        url = yes24_base_url + '?SearchWord=' + quote(query, encoding='euc-kr')
        # params에 넣으면 인코딩문제 발생.. 해결 필요

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Referer': 'http://www.yes24.co.kr/Mall/BuyBack/Search?CategoryNumber=018',
        }
        params = {
            'CategoryNumber': '018',
            'SearchDomain': 'BOOK',  # 국내도서
            'BuybackAccept': 'Y',
            'pageIndex': page,
        }
        self.link = url+'&'+urlencode(params)

        response = requests.get(url, headers=headers, params=params)
        return response

    def get_result_count(self, soup):
        result_count = soup.select('div.rstTxt > h3 > strong:nth-of-type(2)')
        if result_count:
            return result_count[0].text
        else:
            return None

    def crawl(self, soup, query, cur_page, num_pages):
        """Crawl until the end of list in yes24"""
        while True:
            for tag in soup.select(".bbGoodsList ul.clearfix li"):
                image_v = tag.select('div.bbG_img img')[0].get('src')
                title_v = tag.select('div.bbG_info a')[0].get('title')
                author_v = tag.select('span.bbG_auth')[0].text
                publisher_v = tag.select('span.bbG_pub')[0].text
                pubdate_v = tag.select('span.bbG_date')[0].text
                prices = tag.select('div.bbG_price td')
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(map(lambda p:p.text, prices))
                yield {
                    'image':image_v,
                    'title':title_v,
                    'author':author_v,
                    'publisher':publisher_v,
                    'pubdate':pubdate_v,
                    'prices':prices_v,
                    'platform':'yes24',
                    'page':cur_page,
                    'link':self.link,
                }
            cur_page += 1
            if cur_page > num_pages:
                break
            soup = self.get_soup(self.get_response(query, cur_page))


class AladinCrawl(Crawl):
    def __init__(self):
        # self.base_url = aladin_base_url
        self.items_per_page = 10

    def get_response(self, query, page):
        url = aladin_base_url + '?KeyWord=' + quote(query, encoding="euc-kr")
        # params에 넣으면 인코딩문제 발생.. 해결 필요

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Referer': 'http://www.aladin.co.kr/shop/usedshop/wc2b_gate.aspx',
        }
        params = {
           'ActionType': 1,
           'SearchTarget': 'Book',   # 국내도서
           'page': page,
        }
        self.link = url+'&'+urlencode(params)
        response = requests.get(url, headers=headers, params=params)
        return response

    def get_result_count(self, soup):
        result_count = soup.select('#pnItemList > table strong')
        if result_count:
            return result_count[1].text
        else:
            return None

    def crawl(self, soup, query, cur_page, num_pages):
        """Crawl until the end of list in aladin"""
        while True:
            items = soup.select('#searchResult > tr')
            tags = (t for t in items if items.index(t)%2==0)
            for tag in tags:
                image_v = tag.select('td img')[0].get('src')
                title_v = tag.select('td > a > strong')[0].text
                # link =
                # author, publisher, pubdate는 한번에 처리
                pubinfo = tag.select('td')[3].find_all(text=True)[:-1]
                pubinfo = pubinfo[3:] if pubinfo[2].startswith(' -') else pubinfo[2:]
                *author, publisher_v, pubdate = pubinfo
                author_v = ''.join(author).rstrip(' | ')
                pubdate_v = pubdate.lstrip(" | ")
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(p.text for p in tag.select('.c2b_tablet3'))
                yield {
                    'image':image_v,
                    'title':title_v,
                    'author':author_v,
                    'publisher':publisher_v,
                    'pubdate':pubdate_v,
                    'prices':prices_v,
                    'platform':'aladin',
                    'page':cur_page,
                    'link':self.link,
                }
            cur_page += 1
            if cur_page > num_pages:
                break
            soup = self.get_soup(self.get_response(query, cur_page))
