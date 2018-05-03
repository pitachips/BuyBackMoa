import requests

from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import Request, urlopen


yes24_base_url = 'http://www.yes24.co.kr/Mall/buyback/Search'
aladin_base_url = 'http://used.aladin.co.kr/shop/usedshop/wc2b_search.aspx'


def select_yes24(soup, page, link):
    books = []
    for tag in soup.select(".bbGoodsList ul.clearfix li"):
        image_v = tag.select('div.bbG_img img')[0].get('src')
        title_v = tag.select('div.bbG_info a')[0].get('title')
        author_v = tag.select('span.bbG_auth')[0].text
        publisher_v = tag.select('span.bbG_pub')[0].text
        pubdate_v = tag.select('span.bbG_date')[0].text
        prices = tag.select('div.bbG_price td')
        # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
        prices_v = list(map(lambda p: p.text, prices))
        book = {
            'image': image_v,
            'title': title_v,
            'author': author_v,
            'publisher': publisher_v,
            'pubdate': pubdate_v,
            'prices': prices_v,
            'platform': 'yes24',
            'page': page,
            'link': link,
        }
        books.append(book)
    # print(books)
    return books


def select_aladin(soup, page, link):
    books = []
    items = soup.select('#searchResult > tr')
    tags = (t for t in items if items.index(t) % 2 == 0)
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
        book = {
            'image': image_v,
            'title': title_v,
            'author': author_v,
            'publisher': publisher_v,
            'pubdate': pubdate_v,
            'prices': prices_v,
            'platform': 'aladin',
            'page': page,
            'link': link,
        }
        books.append(book)
    # print(books)
    return books


def crawl_yes24(searchword, page):
    url = yes24_base_url + '?SearchWord=' + quote(searchword, encoding='euc-kr')
    # params에 넣으면 인코딩문제 발생.. 해결 필요

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Referer': 'http://www.yes24.co.kr/Mall/BuyBack/Search?CategoryNumber=018',
    }
    params = {
        'CategoryNumber':'018',
        'SearchDomain':'BOOK',  # 국내도서
        'BuybackAccept':'Y',
        'pageIndex':page,
    }
    response = requests.get(url, headers=headers, params=params)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    item = select_yes24(soup, page, response.url)
    return item



def crawl_aladin(searchword, page):
    url = aladin_base_url + '?KeyWord=' + quote(searchword, encoding="euc-kr") + '&ActionType=1&SearchTarget=Book&page='
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Referer':url + str(page-1),
        # 'Connection':'close'
    }
    # params = {
    #     'ActionType':1,
    #     'SearchTarget':'Book',  # 국내도서
    #     'page':page,
    # }
    # response = requests.get(url+str(page), headers=headers)
    req = Request(url=url+str(page), headers=headers)
    response = urlopen(req)
    # response = urlopen(url)  ## 헤더 다 필요없이 그냥 보내기
    html = response.read().decode('euc-kr')
    soup = BeautifulSoup(html, 'html.parser')
    item = select_aladin(soup, page, response.url)
    return item

