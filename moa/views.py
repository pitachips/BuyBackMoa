import re
import requests

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from bs4 import BeautifulSoup
from math import ceil
from urllib.parse import quote


# Create your views here

def soupify(base_url, page):
    """Make each page into BeautifulSoup object"""
    url = base_url + str(page)
    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def yes24_crawl(soup, resultset, page=1, items_per_page=20):
    """Crawl until the end of list in yes24"""
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

            resultset.append({
                'image':image_v,
                'title':title_v,
                'author':author_v,
                'publisher':publisher_v,
                'pubdate':pubdate_v,
                'prices':prices_v,
                'platform':'yes24',
                'page':page,
                })
    except IndexError:
        pass


def aladin_crawl(soup, resultset, page=1, items_per_page=10):
    """Crawl until the end of list in aladin"""
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
            author_v = str_join[:str_join.index("|")-1]
            publisher_v = auth_and_pub[-3]
            pubdate_v = auth_and_pub[-2].lstrip(" | ")
            # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
            prices_v = list(map(lambda p:p.text, prices[4*i:4*(i+1)]))

            resultset.append({
                'image':image_v,
                'title':title_v,
                'author':author_v,
                'publisher':publisher_v,
                'pubdate':pubdate_v,
                'prices':prices_v,
                'platform':'aladin',
                'page':page,
                })
    except IndexError:
        pass


def index(request):
    return render(request, 'moa/index.html')


def result(request):
    query = request.GET.get('searchword')

    # yes24 크롤링 파트
    yes24_resultset = []

    # yes24 바이백 기본 url 세팅
    # yes24도 euc-kr로 인코딩 가능. 단 url 상에는 utf-16-be 인코딩으로 나타나서 혼란 유발..
    yes24_base_url = 'http://www.yes24.com/Mall/buyback/Search' \
        '?CategoryNumber=018&SearchDomain=BOOK&BuybackAccept=Y' \
        '&SearchWord=' + quote(query, encoding="euc-kr") + '&pageIndex='
    yes24_soup = soupify(yes24_base_url, 1)

    yes24_result_count_wrap = yes24_soup.select(
        'div.rstTxt > h3 > strong:nth-of-type(2)'
    )
    if yes24_result_count_wrap:
        yes24_result_count = int(re.search(r'\d+', yes24_result_count_wrap[0].text)[0])
        if yes24_result_count > 100:
            context = {
                'advice':"결과가 너무 많습니다. 보다 구체적으로 검색해 주세요"
            }
            return render(request, 'moa/index.html', context)
        else:
            num_pages = ceil(yes24_result_count/20)
            yes24_crawl(yes24_soup, yes24_resultset)
            for page in range(2, num_pages):
                yes24_soup = soupify(yes24_base_url, page)
                yes24_crawl(yes24_soup, yes24_resultset, page)
    else:
        # 검색 결과 없음
        pass


#aladin 크롤링 파트
    aladin_resultset = []

    # aladin 바이백 기본 url 세팅
    aladin_base_url = 'http://used.aladin.co.kr/shop/usedshop/wc2b_search.aspx' \
        '?ActionType=1&SearchTarget=Book&x=0&y=0' \
        '&KeyWord=' + quote(query, encoding="euc-kr") + '&page='
    aladin_soup = soupify(aladin_base_url, 1)

    aladin_result_count_wrap = aladin_soup.select(
        '#pnItemList > table:nth-of-type(1) > tr > td:nth-of-type(1) > strong'
        )
    if aladin_result_count_wrap:
        aladin_result_count = int(re.search(r'\d+', aladin_result_count_wrap[0].text)[0])
        if aladin_result_count > 200:
            context = {
                'advice':"결과가 너무 많습니다. 보다 구체적으로 검색해 주세요"
            }
            return render(request, 'moa/index.html', context)
        else:
            num_pages = ceil(aladin_result_count/10)
            aladin_crawl(aladin_soup, aladin_resultset)
            for page in range(2, num_pages):
                aladin_soup = soupify(aladin_base_url, page)
                aladin_crawl(aladin_soup, aladin_resultset, page)
    else:
        #검색결과 없음
        pass


# page번호 순서대로 정렬
    total_resultset = yes24_resultset + aladin_resultset
    total_resultset = sorted(total_resultset, key=lambda rs : rs['page'])

# pagination 하여 뿌리기
    page = request.GET.get('page')
    pagniator = Paginator(total_resultset, 20)
    try:
        total_resultset_paged = pagniator.page(page)
    except PageNotAnInteger:
        total_resultset_paged = pagniator.page(1)
    except EmptyPage:
        total_resultset_paged = paginator.page(pagniator.num_pages)

    context = {
        'total_resultset_paged': total_resultset_paged,
        'yes24_base_url': yes24_base_url,
        'aladin_base_url': aladin_base_url,
    }

    return render(request, 'moa/search_result.html', context)



### 앞으로 할 일(BACK)
# TODO: 결과가 없을 때 취할 모션은?
# TODO: 향후 동일 책을 기준으로 알리딘 vs yes24 vs 인터파크로 보여줘야
# TODO: 향후 interpark 중고도서 서비스 추가

# TODO: total_resultset 정렬 기준 고민 필요

# TODO: 향후 DB에 저장해놓고 매일 자정에 DB 업데이트 하는 방향으로 개선?

# TODO: 정확도가 높은 각 사이트별 50개 자료만 보여준다고 양해문구 삽입하는 것도 방법
# TODO: 알라딘과 yes24를 병렬적으로 크롤링 하도록 구성
## TODO: 프론트에서 ajax로 페이지네이션 구현?
## TODO: 여러번 긁어오는거 절대 안됨

# TODO: admin 필요성 고민

#### TODO: 프론트에 부트스트랩 적용