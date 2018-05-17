import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from unittest import skip


options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--window-size=1920x1080')
options.add_argument('--disable-gpu')


class NewVisitorTest(StaticLiveServerTestCase):

    def send_searchword_to_searchbox(self, searchword, timeout=5, clearup=True):
        searchbox = self.browser.find_element_by_id('searchbox')
        if clearup:
            searchbox.clear()
        searchbox.send_keys(searchword)  # '파이썬을 이용한 테스트 주도 개발' 의 ISBN
        searchbox.send_keys(Keys.ENTER)
        self.browser.set_page_load_timeout(timeout)

    def setUp(self):
        self.browser = webdriver.Chrome(chrome_options=options)
        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = staging_server
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()


    def test_layout_and_static_files(self):
        self.browser.get(self.live_server_url)
        # 이 곳이 바이백 모아 임을 확인한다
        self.assertIn('바이백 모아', self.browser.title)
        # 현재 서비스 중인 온라인 서점의 로고가 잘 보인다.
        logos = self.browser.find_elements_by_class_name('logo')
        self.assertTrue(any('/static/image/yes24_logo.png' in logo.get_attribute('src') for logo in logos))
        self.assertTrue(any('/static/image/aladin_logo.png' in logo.get_attribute('src') for logo in logos))
        # 검색창의 placeholder가 잘 있는지 확인한다
        searchbox = self.browser.find_element_by_id('searchbox')
        self.assertEqual(searchbox.get_attribute('placeholder'), '책 제목, 저자, ISBN 등')


    def test_basic_search(self):
        self.browser.get(self.live_server_url)
        # 검색창에 '특허법' 을 입력하고 전송한다. 결과는 5초의 시간 내에 렌더되어야 한다.
        self.send_searchword_to_searchbox('특허법', 5)
        # 그러면 알라딘 및 예스24에서 바이백 가능한 특허법 관련 책 리스트가 나온다. 그 리스트는 최대 20개 아이템을 가지고 있다.
        books = self.browser.find_elements_by_class_name('row')
        self.assertLessEqual(len(books), 20)
        # 페이지 맨 하단으로 내려가서 next 페이지가 있는지 확인하고, 있으면 next를 눌러본다.
        next = self.browser.find_element_by_class_name('page-link')
        self.assertEqual(next.text, '▶')
        cur_url = self.browser.current_url
        self.assertEqual(cur_url + '&page=2', next.get_attribute('href'))
        # next 페이지에 나타난 첫번째 아이템이 선우가 팔려고 했던 책이다.
        buyback_link = self.browser.find_element_by_css_selector('.row .col-md-9 a')
        #  표시된 링크와 실제 연결된 링크가 해당 인터넷 사이트로 연결되는지 확인한다.
        if 'yes24' in buyback_link.text:
            self.assertIn('yes24', buyback_link.get_attribute('href'))
        elif 'aladin' in buyback_link.text:
            self.assertIn('aladin', buyback_link.get_attribute('href'))
        else:
            self.fail()
        # '팔기' 링크가 새로운 탭으로 열어지는지도 확인한다. 잚 만들었다고 생각한다.
        self.assertEqual(buyback_link.get_attribute('target'), '_blank')
        # 검색창에 여전히 '특허법'이 출력되어 있는 것을 확인한다
        searchbox = self.browser.find_element_by_id('searchbox')
        self.assertEqual(searchbox.get_attribute('value'), '특허법')
        # 이제 'introduction to algorithms'을 판매하려고 한다. 우선 검색창을 깨끗이 하고 검색한다.결과는 5초의 시간 내에 렌더되어야 한다.
        self.send_searchword_to_searchbox('introduction to algorithms', 5)
        # 검색 리스트 페이지가 출력되는 것을 확인한다.
        self.assertIn('result/?searchword=introduction+to+algorithms', self.browser.current_url)
        # 이제 홈버튼을 눌러 메인화면으로 돌아간다.
        home_button = self.browser.find_element_by_id('to-home')
        home_button.click()
        subject = self.browser.find_element_by_tag_name('h1')
        self.assertEqual(subject.text, '중고책 매입가 검색')
        # 처음에 검색했던 '특허법'을 다시 검색한다. 결과는 1초의 시간 내에 렌더되어야 한다.
        self.send_searchword_to_searchbox('특허법', 1)
        # 이제 ISBN으로 검색을 해보고자 한다
        self.send_searchword_to_searchbox('9788994774916', 5)
        # ISBN에 대한 책은 하나밖에 없으므로 리스트 최대길이는 2를 넘으면 안 된다.
        books = self.browser.find_elements_by_class_name('row')
        self.assertLessEqual(len(books), 2)


    def test_identical_item_is_served_from_memcached_to_different_browsers(self):
        # 크롬에서 '고성능 파이썬'을 검색한다.
        self.browser.get(self.live_server_url)
        self.send_searchword_to_searchbox('고성능 파이썬', 5)
        # 크롬 종료
        self.browser.quit()
        # 사파리를 열고, '고성능 파이썬'을 검색한다.
        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser.get(self.live_server_url)
        # 아주 빠른 시간 내에 리턴되어야 한다.
        self.send_searchword_to_searchbox('고성능 파이썬', 1)

    def test_empty_searchword_cannot_be_submitted(self):
        self.browser.get(self.live_server_url)
        before = self.live_server_url
        self.send_searchword_to_searchbox('', 5)
        self.assertEqual(before + '/', self.browser.current_url)
