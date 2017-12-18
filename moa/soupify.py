import requests
from urllib.parse import quote

from bs4 import BeautifulSoup


def soupify(flag, base_url, query, page):
    """Make each page into BeautifulSoup object"""
    if flag == 'yes24':
        url = base_url + quote(query, encoding="euc-kr") + '&pageIndex=' + str(page)
    elif flag == 'aladin':
        url = base_url + quote(query, encoding="euc-kr") + '&page='
    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup
