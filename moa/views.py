import json

from itertools import chain
from urllib.parse import quote

from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from .crawlers import Yes24Crawl, AladinCrawl, yes24_base_url, aladin_base_url

# Create your views here


def index(request):
    return render(request, 'moa/index.html')


def result(request):
    query = request.GET.get('searchword')
    key = query.replace(" ",".")
    content_j = cache.get(key)
    if content_j is None:
        # yes24 크롤링 결과
        yes24_crawler = Yes24Crawl()
        yes24_resultset = yes24_crawler(query)
        # aladin 크롤링 결과
        aladin_crawler = AladinCrawl()
        aladin_resultset = aladin_crawler(query)
        # yes24 및 aladin 모두 검색 결과가 없는 경우
        if yes24_resultset is None and aladin_resultset is None:
            return render(request, 'moa/index.html', context={
                'advice':"검색 결과 0건",
            })
        # page번호 순서대로 정렬된 total_resultset 만들기
        total_resultset = list(yes24_resultset) + list(aladin_resultset)
        total_resultset = sorted(total_resultset, key=lambda rs : rs['page'])
        # 캐시에 저장
        content_j = json.dumps(total_resultset)
        cache.set(key, content_j, 60*5)

    # 페이지네이션
    page = request.GET.get('page')
    content = json.loads(content_j)
    paginator = Paginator(content, 20)
    try:
        total_resultset_paged = paginator.page(page)
    except PageNotAnInteger:
        total_resultset_paged = paginator.page(1)
    except EmptyPage:
        total_resultset_paged = paginator.page(paginator.num_pages)

    # 렌더하기
    context = {
        'total_resultset_paged': total_resultset_paged,
        'yes24_url': yes24_base_url + quote(query, encoding="euc-kr") + '&pageIndex=',
        'aladin_url': aladin_base_url + quote(query, encoding="euc-kr") + '&page=',
    }
    return render(request, 'moa/search_result.html', context)



### 앞으로 할 일(BACK)
# TODO: 결과가 없을 때 취할 모션은?
# TODO: 향후 interpark 중고도서 서비스 추가

# TODO: total_resultset 정렬 기준 고민 필요 - 판매서점별 / 정확도순 / 가격순 / ?

# TODO: 캐시 종류를 공부해서 알맞은 캐시 찾기 settings에 반영. Memcached가 적정해보임.

### TODO: 알라딘과 yes24를 병렬적으로 크롤링 하도록 구성
##### TODO: 프론트에서 ajax로 페이지네이션 구현?
# TODO: 첫번째 페이지 로딩 속도를 빠르게 하기 위한 방법 모색
# TODO: 전면적 리팩토링 필요(기준: 가독성, 검색속도, cpu자원`)

# TODO: admin 필요성 고민

# TODO: README 작성
