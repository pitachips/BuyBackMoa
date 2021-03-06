from typing import Any, List
from concurrent import futures
from itertools import zip_longest
from urllib.parse import quote
from django.core.exceptions import RequestDataTooBig
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import render

import ring

from .crawlers import crawl_yes24, crawl_aladin, yes24_base_url, aladin_base_url


def index(request):
    return render(request, 'moa/index.html')


@ring.django.cache(expire=30 * 60, coder="json")  # 단위는 초
def search_books(query: str) -> List[Any]:
    total_resultset = []
    with futures.ThreadPoolExecutor(max_workers=6) as exe:
        # NOTE: 알라딘 6페이지, 예스24 4페이지는 자의적인 넘버
        fs = tuple(filter(None, sum(zip_longest([exe.submit(crawl_aladin, query, page) for page in range(1, 6)],
                                                [exe.submit(crawl_yes24, query, page) for page in range(1, 4)]), ())))
        done, undone = futures.wait(fs, timeout=3)
        if undone:
            for f in undone:
                f.cancel()
        for f in done:
            total_resultset += f.result()
    return total_resultset


def result(request):
    # t1 = time.time()
    query = request.GET.get('searchword')
    # TODO: validator 작성? [a-zA-Aㄱ-힣0-9-_!@#$%&*()=+.,/?'";:[]{}~₩]  // &# 비허용

    if not query:
        raise Http404()

    if len(query.encode("utf8")) > 100:  # ring에서 prefix를 붙이므로 적절히 100으로 한다
        raise RequestDataTooBig('Memcached key length must be less than 100 bytes')

    key = query.strip().replace(" ", ".")
    total_resultset = search_books(key)

    page = request.GET.get('page')
    paginator = Paginator(total_resultset, 20)
    try:
        total_resultset_paged = paginator.page(page)
    except PageNotAnInteger:
        total_resultset_paged = paginator.page(1)
    except EmptyPage:
        total_resultset_paged = paginator.page(paginator.num_pages)

    context = {
        'total_resultset_paged': total_resultset_paged,
        'yes24_url': yes24_base_url + quote(query, encoding="euc-kr"),
        'aladin_url': aladin_base_url + quote(query, encoding="euc-kr"),
    }
    # print(time.time()-t1, '초, 총 소요시간')

    return render(request, 'moa/search_result.html', context)
