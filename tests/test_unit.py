# from django.http import HttpRequest
# from django.core.urlresolvers import resolve  ## deprecated since django 1.10
from django.urls import resolve, reverse
from django.test import TestCase
from moa.views import index as view_index, result as view_result
from unittest import skip


class IndexPageTest(TestCase):
    def test_root_url_resolves_to_index_view(self):
        found = resolve('/')
        self.assertEqual(found.func, view_index)

    def test_index_page_uses_index_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'moa/index.html')


class ResultPageTest(TestCase):
    def test_result_url_resolves_to_result_view(self):
        found = resolve('/result/')
        self.assertEqual(found.func, view_result)

    def test_result_page_uses_search_result_template(self):
        response = self.client.get('/result/?searchword=아무거나')
        self.assertTemplateUsed(response, 'moa/search_result.html')

    def test_empty_searchword_raises_http404(self):  # not found
        # with self.assertRaises(Http404):
        response = self.client.get(reverse('result'), {})
        self.assertEqual(response.status_code, 404)

    def test_searchword_gt_250bytes_throws_http400(self):  # bad request
        # 100byte 미만까지만 허용. nul-terminator가 2 바이트 차지. 영문자는 1바이트. 한글은 3바이트 차지
        response = self.client.get(reverse('result'), {'searchword': 'a' * 101, })
        self.assertEqual(response.status_code, 400)
        response = self.client.get(reverse('result'), {'searchword': '가' * 34, })
        self.assertEqual(response.status_code, 400)

    def test_searchword_lt_100bytes_silently_succeeds(self):
        response = self.client.get(reverse('result'), {'searchword': 'a' * 97, })
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('result'), {'searchword': '가' * 32, })
        self.assertEqual(response.status_code, 200)

    def test_empty_searchword_returns_http404(self):
        response = self.client.get(reverse('result'), {'searchword': ''})
        self.assertEqual(response.status_code, 404)

    def test_edge_case_searchwords_return_http200(self):
        response = self.client.get(reverse('result'), {'searchword': '??????'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('result'), {'searchword': '&#9232;'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('result'), {'searchword': '!#@^#%\'?>"25뛟"'})
        self.assertEqual(response.status_code, 200)
