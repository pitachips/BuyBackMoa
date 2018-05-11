import json
# import time
from concurrent import futures
from itertools import zip_longest
from urllib.parse import quote
from django.core.cache import cache
from django.core.exceptions import RequestDataTooBig
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import render
from .crawlers import crawl_yes24, crawl_aladin, yes24_base_url, aladin_base_url


def index(request):
    return render(request, 'moa/index.html')


def result(request):
    # t1 = time.time()
    query = request.GET.get('searchword')
    # validator 작성? [a-zA-Aㄱ-힣0-9-_!@#$%&*()=+.,/?'";:[]{}~₩]  // &# 비허용
    if not query:
        raise Http404()
    if len(query.encode()) > 97:
        raise RequestDataTooBig('Memecached key length must be less than 100 bytes')

    total_resultset = []
    key = query.strip().replace(" ", ".")
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
        'yes24_url': yes24_base_url + quote(query, encoding="euc-kr"),
        'aladin_url': aladin_base_url + quote(query, encoding="euc-kr"),
    }
    # print(time.time()-t1, '초, 총 소요시간')

    return render(request, 'moa/search_result.html', context)
