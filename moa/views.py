import json
import time
from concurrent import futures
from itertools import zip_longest
from urllib.parse import quote
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from .crawlers import crawl_yes24, crawl_aladin, yes24_base_url, aladin_base_url


def index(request):
    return render(request, 'moa/index.html')


def result(request):
    t1 = time.time()

    query = request.GET.get('searchword')
    total_resultset = []
    key = query.strip().replace(" ",".")
    content_j = cache.get(key)

    if content_j is None:
        with futures.ThreadPoolExecutor(max_workers=6) as exe:
            fs = tuple(filter(None, sum(zip_longest([exe.submit(crawl_aladin, query, page) for page in range(1, 6)],
                                                    [exe.submit(crawl_yes24, query, page) for page in range(1, 4)]), ())))
            # for f in futures.as_completed(fs, timeout=4):
            #     total_resultset += f.result()
            done, undone = futures.wait(fs, timeout=3)
            if undone:
                for f in undone:
                    print(f'{f} is cancelled')
                    f.cancel()
            for f in done:
                total_resultset += f.result()

        content_j = json.dumps(total_resultset)
        cache.set(key, content_j, 60*5)
    content = json.loads(content_j)

    page = request.GET.get('page')
    paginator = Paginator(content, 20)
    try:
        total_resultset_paged = paginator.page(page)
    except PageNotAnInteger:
        total_resultset_paged = paginator.page(1)
    except EmptyPage:
        total_resultset_paged = paginator.page(paginator.num_pages)

    context = {
        'total_resultset_paged': total_resultset_paged,
        'yes24_url': yes24_base_url + quote(query, encoding="euc-kr") ,
        'aladin_url': aladin_base_url + quote(query, encoding="euc-kr"),
    }
    # print(time.time()-t1, '초, 총 소요시간')

    return render(request, 'moa/search_result.html', context)



### 앞으로 할 일(BACK)
# TODO: total_resultset 정렬 기준 고민 필요 - 판매서점별 / 정확도순 / 가격순 / ?
# TODO: 캐시 종류를 공부해서 알맞은 캐시 찾기 settings에 반영. Memcached가 적정해보임.
# TODO: 프론트에서 ajax로 페이지네이션 구현?
# TODO: 프론트에서 알라딘 vs yes24로 2단 구성하기
# TODO: 로딩 되는 동안 뱅글뱅글 돌아가는 이미지
# TODO: 서빙을 async 하게 할 필요 있음 aiohttp 모듈 참고하기
# TODO: 첫번째 페이지 로딩 속도를 빠르게 하기 위한 방법 모색 - 뷰티풀숩 텍스트 서칭 속드를 개선?
# TODO: admin 필요성 고민
# TODO: README 작성
