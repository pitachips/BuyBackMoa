from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re


# Create your views here.

def index(request):
    return render(request, 'moa/index.html')


def result(request):
    query = request.GET.get('searchword')

    # 크롤링 파트
    yes24_resultset = []

    # yes24 바이백 기본 url 세팅
    # yes24도 euc-kr로 인코딩 가능. 단 url 상에는 utf-16-be 인코딩으로 나타나서 혼란 유발..
    yes24_base_url = 'http://www.yes24.com/Mall/buyback/Search' \
        '?CategoryNumber=018&SearchDomain=BOOK&BuybackAccept=Y' \
        '&SearchWord=' + quote(query, encoding="euc-kr") + '&pageIndex='

    yes24_page = 1
    while yes24_page > 0:
        # TODO: 아래 네 줄은 def soupify 로 캡슐화 가능
        yes24_url = yes24_base_url + str(yes24_page)
        yes24_req = requests.get(yes24_url)
        yes24_html = yes24_req.text
        yes24_soup = BeautifulSoup(yes24_html, 'html.parser')

        # yes24의 결과 개수
        try:
            result_count = yes24_soup.select(
                'div.rstTxt > h3 > strong:nth-of-type(2)'
                )[0].get_text()
            if int(re.search(r'\d+', result_count)[0]) > 100:
                context = {
                    'advice':"결과가 너무 많습니다. 보다 구체적으로 검색해 주세요"
                }
                return render(request, 'moa/index.html', context)
        except IndexError:
            yes24_page = -100

        # 추후 빠른시일내 아래 내용 효율화 필요. 그냥 리스트 형태로 다 받아서 처리할 건지
        try:
            for i in range(1,21):
                image = yes24_soup.select(
                    'ul.clearfix li:nth-of-type(' + str(i) + ') div.bbG_img img'
                    )
                image_v = image[0].get('src')
                title = yes24_soup.select(
                    'ul.clearfix li:nth-of-type(' + str(i) + ') div.bbG_info a'
                    )
                title_v = title[0].get('title')
                prices = yes24_soup.select(
                    'ul.clearfix li:nth-of-type(' +str(i) + ') div.bbG_price td'
                    )
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(map(lambda p:p.text, prices))

                yes24_resultset.append({
                    'image':image_v,
                    'title':title_v,
                    'prices':prices_v,
                    'platform':'yes24',
                    'page':yes24_page,
                    })

        except IndexError:
            yes24_page = -100

        yes24_page += 1


    aladin_resultset = []

    # aladin 바이백 기본 url 세팅
    aladin_base_url = 'http://used.aladin.co.kr/shop/usedshop/wc2b_search.aspx' \
        '?ActionType=1&SearchTarget=Book&x=0&y=0' \
        '&KeyWord=' + quote(query, encoding="euc-kr") + '&page='

    aladin_page = 1
    while aladin_page > 0:
        # aladin도 euc-kr로 인코딩하여 검색
        aladin_url = aladin_base_url + str(aladin_page)
        aladin_req = requests.get(aladin_url)
        aladin_html = aladin_req.text
        aladin_soup = BeautifulSoup(aladin_html, 'html.parser')

        # aladin의 결과 개수
        try:
            result_count = aladin_soup.select(
                '#pnItemList > table:nth-of-type(1) > tr > td:nth-of-type(1)'
                + ' > strong')[0].get_text()
            if int(re.search(r'\d+', result_count)[0]) > 200:
                context = {
                    'advice':"결과가 너무 많습니다. 보다 구체적으로 검색해 주세요"
                }
                return render(request, 'moa/index.html', context)
        except IndexError:
            aladin_page = -100

        # 추후 빠른시일내 아래 내용 효율화 필요. 그냥 리스트 형태로 한꺼번에 받아서 처리할 건지... prices 처럼
        try:
            prices = aladin_soup.select('#searchResult .c2b_tablet3')
            for i in range(10):
                image = aladin_soup.select('#searchResult td img')
                image_v = image[i].get('src')
                title = aladin_soup.select('#searchResult td > a > strong')
                title_v = title[i].text
                # prices_v 인덱스: 0 정가, 1 바이백 최상 , 2 바이백 상, 3 바애빅 중
                prices_v = list(map(lambda p:p.text, prices[4*i:4*(i+1)]))

                aladin_resultset.append({
                    'image':image_v,
                    'title':title_v,
                    'prices':prices_v,
                    'platform':'aladin',
                    'page':aladin_page,
                    })

        except IndexError:
            aladin_page = -100

        aladin_page += 1


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
# TODO: 크롤링 부분을 함수화 할지 그냥 냅둘지 고민 필요
# TODO: 서치할 때 모든 자료를 다 받아오는 오버헤드 발생 방지 필요
# TODO: 정확도가 높은 각 사이트별 50개 자료만 보여준다고 양해문구 삽입하는 것도 방법
# TODO: total_resultset 정렬 기준 고민 필요

# TODO: 향후 동일 책을 기준으로 알리딘 vs yes24 vs 인터파크로 보여줘야
# TODO: 향후 DB에 저장해놓고 매일 자정에 DB 업데이트 하는 방향으로 개선
# TODO: 알라딘과 yes24를 병렬적으로 크롤링 하도록 구성
# TODO: 향후 interpark 중고도서 서비스 추가

# TODO: 프론트에 부트스트랩 적용