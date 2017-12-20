from .soupify import soupify
from math import ceil
import re


##### yes24 크롤러 #####

yes24_base_url = 'http://www.yes24.com/Mall/buyback/Search' \
    '?CategoryNumber=018&SearchDomain=BOOK&BuybackAccept=Y' \
    '&SearchWord='

def yes24_crawl(soup, query, num_pages):
    """Crawl until the end of list in yes24"""
    cur_page = 1
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
            }
        cur_page += 1
        if cur_page > num_pages:
            break
        soup = soupify('yes24', yes24_base_url, query, cur_page)


def yes24_check_and_crawl(query):
    soup = soupify('yes24', yes24_base_url, query, 1)
    result_count = soup.select('div.rstTxt > h3 > strong:nth-of-type(2)')[0].text
    if result_count:
        # yes24 검색 결과 건수에 따른 분기
        result_count = int(re.search(r'\d+', result_count)[0])
        if result_count > 150:
            # 150건 초과
            return "too much"
        else:
            # 1건 이상 150건 이하
            num_pages = ceil(result_count/20)
            return yes24_crawl(soup, query, num_pages)
    else:
        return None   # 0건의 검색 결과



##### aladin크롤러 #####

aladin_base_url = 'http://used.aladin.co.kr/shop/usedshop/wc2b_search.aspx' \
    '?ActionType=1&SearchTarget=Book&x=0&y=0' \
    '&KeyWord='


def aladin_crawl(soup, query, num_pages):
    """Crawl until the end of list in aladin"""
    # aladin_resultset = []
    cur_page = 1
    while True:
        items = soup.select('#searchResult > tr')
        tags = (t for t in items if items.index(t)%2==0)
        for tag in tags:
            image_v = tag.select('td img')[0].get('src')
            title_v = tag.select('td > a > strong')[0].text
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
            }
        cur_page += 1
        if cur_page > num_pages:
            break
        soup = soupify('aladin', aladin_base_url, query, cur_page)


def aladin_check_and_crawl(query):
    soup = soupify('aladin', aladin_base_url, query, 1)
    result_count = soup.select('#pnItemList > table strong')[1].text
    if result_count:
        # aladin 검색 결과 건수에 따른 분기
        result_count = int(re.search(r'\d+', result_count)[0])
        if result_count > 200:
            # 200건 초과
            return "too much"
        else:
            # 1건 이상 200건 이하
            num_pages = ceil(result_count/10)
            return aladin_crawl(soup, query, num_pages)
    else:
        return None  # 0건의 검색 결과
