from .soupify import soupify
from math import ceil
import re

# TODO: 크롤링된 내용 일부를 박싱하고 한번에 훑는 걸로 변경



##### yes24 크롤러 #####

yes24_base_url = 'http://www.yes24.com/Mall/buyback/Search' \
        '?CategoryNumber=018&SearchDomain=BOOK&BuybackAccept=Y' \
        '&SearchWord='

def yes24_crawl(soup, query, num_pages):
    """Crawl until the end of list in yes24"""
    yes24_resultset = []
    items_per_page = 20
    cur_page = 1
    while cur_page <= num_pages:
        try:
            for i in range(1,items_per_page+1):
                image = soup.select(
                    'ul.clearfix li:nth-of-type(' + str(i) + ') div.bbG_img img'
                    )
                image_v = image[0].get('src')
                title = soup.select(
                    'ul.clearfix li:nth-of-type(' + str(i) + ') div.bbG_info a'
                    )
                title_v = title[0].get('title')
                author = soup.select(
                    'div.bbGoodsList > ul > li:nth-of-type(' + str(i) + ') span.bbG_auth'
                    )
                author_v = author[0].text
                publisher = soup.select(
                    'div.bbGoodsList > ul > li:nth-of-type(' + str(i) + ') span.bbG_pub'
                    )
                publisher_v = publisher[0].text
                pubdate = soup.select(
                    'div.bbGoodsList > ul > li:nth-of-type(' + str(i) + ') span.bbG_date'
                    )
                pubdate_v = pubdate[0].text
                prices = soup.select(
                    'ul.clearfix li:nth-of-type(' +str(i) + ') div.bbG_price td'
                    )
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(map(lambda p:p.text, prices))

                yes24_resultset.append({
                    'image':image_v,
                    'title':title_v,
                    'author':author_v,
                    'publisher':publisher_v,
                    'pubdate':pubdate_v,
                    'prices':prices_v,
                    'platform':'yes24',
                    'page':cur_page,
                    })
        except IndexError:
            print("인덱스 에러!")
        cur_page += 1
        soup = soupify('yes24', yes24_base_url, query, cur_page)
    return yes24_resultset


def yes24_check_and_crawl(query):
    yes24_soup = soupify('yes24', yes24_base_url, query, 1)
    yes24_result_count_wrap = yes24_soup.select(
            'div.rstTxt > h3 > strong:nth-of-type(2)'
        )
    if yes24_result_count_wrap:
        # yes24 검색 결과 건수에 따른 분기
        yes24_result_count = int(re.search(r'\d+', yes24_result_count_wrap[0].text)[0])
        if yes24_result_count > 150:
            # 150건 초과
            return "too much"
        else:
            # 1건 이상 150건 이하
            num_pages = ceil(yes24_result_count/20)
            return yes24_crawl(yes24_soup, query, num_pages)
    else:
        return None   # 0건의 검색 결과



##### aladin크롤러 #####

aladin_base_url = 'http://used.aladin.co.kr/shop/usedshop/wc2b_search.aspx' \
    '?ActionType=1&SearchTarget=Book&x=0&y=0' \
    '&KeyWord='


def aladin_crawl(soup, query, num_pages):
    """Crawl until the end of list in aladin"""
    aladin_resultset = []
    items_per_page = 10
    cur_page = 1
    while cur_page <= num_pages:
        try:
            prices = soup.select('#searchResult .c2b_tablet3')
            for i in range(items_per_page):
                image = soup.select('#searchResult td img')
                image_v = image[i].get('src')
                title = soup.select('#searchResult td > a > strong')
                title_v = title[i].text
                # author, publisher, pubdate는 한번에 처리
                auth_and_pub = soup.select('#searchResult tr:nth-of-type(' + str(8*i+2) +') br')[0].find_all(text=True)
                str_join = ''.join(auth_and_pub)
                author_v = str_join[:str_join.find("|")-1]
                publisher_v = auth_and_pub[-3]
                pubdate_v = auth_and_pub[-2].lstrip(" | ")
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(map(lambda p:p.text, prices[4*i:4*(i+1)]))
                aladin_resultset.append({
                    'image':image_v,
                    'title':title_v,
                    'author':author_v,
                    'publisher':publisher_v,
                    'pubdate':pubdate_v,
                    'prices':prices_v,
                    'platform':'aladin',
                    'page':cur_page,
                    })
        except IndexError:
            print("인덱스 에러!")
        cur_page += 1
        soup = soupify('aladin', aladin_base_url, query, cur_page)
    return aladin_resultset


def aladin_check_and_crawl(query):
    aladin_soup = soupify('aladin', aladin_base_url, query, 1)
    aladin_result_count_wrap = aladin_soup.select(
            '#pnItemList > table:nth-of-type(1) > tr > td:nth-of-type(1) > strong'
        )
    if aladin_result_count_wrap:
        # aladin 검색 결과 건수에 따른 분기
        aladin_result_count = int(re.search(r'\d+', aladin_result_count_wrap[0].text)[0])
        if aladin_result_count > 200:
            # 200건 초과
            return "too much"
        else:
            # 1건 이상 200건 이하
            num_pages = ceil(aladin_result_count/10)
            return aladin_crawl(aladin_soup, query, num_pages)
    else:
        return None  # 0건의 검색 결과