# -*- coding: utf-8 -*-
import os
import re
import sys
from urllib.parse import quote
from selenium.webdriver.chrome import webdriver
from urllib.parse import urljoin, urlparse
import requests

sys.path.append('/home/ubuntu/django_catfood')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_catfood.settings")
import django
from django_catfood import settings

if 'setup' in dir(django):
    django.setup()

from catfood.models import Brand, ListSelector


def get_brand_list():
    with webdriver.WebDriver() as driver:
        for selector in ListSelector.objects.filter(product_path=""):
            driver.get(selector.base_url)
            data = input(f"{selector.title} 의 상품 리스트 패턴을 입력하세요.\n")
            if data:
                selector.product_path = data.strip()
            selector.save()


def get_urls_list():
    for selector in ListSelector.objects.all():
        pattern = selector.product_path
        pattern = "^"+pattern.replace("**", ".+")+"$"
        brand = Brand.objects.get(english_name=selector.title)
        if re.compile(pattern).fullmatch(brand.url):
            print(re.compile(pattern).fullmatch(brand.url).group())
        else:
            print("shit")
        # break


if __name__ == '__main__':
    get_urls_list()
