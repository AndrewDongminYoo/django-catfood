# -*- coding: utf-8 -*-
import os
import re
import sys
from urllib.parse import quote
from selenium.webdriver.chrome import webdriver
from urllib.parse import urljoin, urlparse
import requests
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidArgumentException
from selenium.common.exceptions import StaleElementReferenceException

sys.path.append('/home/ubuntu/django_catfood')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_catfood.settings")
import django
from django_catfood import settings

if 'setup' in dir(django):
    django.setup()

from catfood.models import Brand, ListSelector, Formula


def get_brand_list():
    with webdriver.WebDriver() as driver:
        for selector in ListSelector.objects.filter(product_path=""):
            driver.get(selector.base_url)
            data = input(f"{selector.title} 의 상품 리스트 패턴을 입력하세요.\n")
            if data:
                selector.product_path = data.strip()
            selector.save()


def google_searching():
    def regex_url(url_regex, target_url):
        pat = "^" + url_regex.replace("**", "[a-zA-Z0-9#?=]+") + "$"
        regex = re.compile(pat)
        if regex.match(target_url):
            return regex.match(target_url).group(0)

    def find_all_urls(w_driver: webdriver.WebDriver, url_string: str):
        try:
            w_driver.get(url_string)
        except InvalidArgumentException as e:
            print(e.msg)
        try:
            return [link.get_attribute("href") for link in w_driver.find_elements(By.CSS_SELECTOR, "a")]
        except StaleElementReferenceException as e:
            print(e.msg)
            soup = BeautifulSoup(w_driver.page_source, "html.parser")
            return [link.get("href") for link in soup.find_all("a")]

    with webdriver.WebDriver() as driver:
        for brand in ListSelector.objects.all():
            pattern = brand.product_path
            all_urls = find_all_urls(driver, brand.base_url)
            print(all_urls)
            for url in all_urls:
                if url and regex_url(pattern, url):
                    Formula.objects.get_or_create(
                        brand=Brand.objects.get(english_name=brand.title),
                        product_url=url
                    )


if __name__ == '__main__':
    google_searching()
