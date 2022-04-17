# -*- coding: utf-8 -*-
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from django.db.models import Q
from requests import Response
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By

from catfood.data import result

sys.path.append('/home/ubuntu/django_catfood')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_catfood.settings")
import django

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


def regex_url(url_regex, target_url):
    if not target_url or type(target_url) is not str:
        return None
    pat = "^" + url_regex.replace("**", "[a-zA-Z0-9#?=]+") + "$"
    regex = re.compile(pat)
    if regex.match(target_url):
        return regex.match(target_url).group(0)


def find_all_urls(w_driver: webdriver.WebDriver, url_string: str):
    try:
        w_driver.get(url_string)
    except InvalidArgumentException as e:
        print(e.msg)
    w_driver.find_elements(By.CSS_SELECTOR, "a")
    soup = BeautifulSoup(w_driver.page_source, "html.parser")
    return [link.get("href") for link in soup.find_all("a")]


def search_urls_by_patterns():
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


def collect_urls_by_patterns():
    with webdriver.WebDriver() as driver:
        for brand, formulas in result.items():
            try:
                target = Brand.objects.get(english_name=brand)
            except Brand.DoesNotExist:
                print(f"{brand} 브랜드가 없습니다.")
                continue
            try:
                selector = ListSelector.objects.get(brand=target)
            except ListSelector.DoesNotExist:
                print(f"{brand} 브랜드 패턴이 없습니다.")
                for formula in formulas:
                    Formula.objects.get_or_create(
                        brand=target,
                        product_url=formula
                    )
                continue
            for formula in formulas:
                try:
                    if regex_url(selector.product_path, formula):
                        formula = formula.split("#")[0]
                        Formula.objects.get_or_create(
                            brand=target,
                            product_url=formula
                        )
                    all_urls = find_all_urls(driver, formula)
                    for url in all_urls:
                        if url and regex_url(selector.product_path, url):
                            url = url.split("#")[0]
                            formulas.append(url) if url not in formulas else None
                            print(url)
                            Formula.objects.get_or_create(
                                brand=target,
                                product_url=url
                            )
                except Exception as e:
                    print(e)
                    continue


def search_crawler():
    for brand in ListSelector.objects.all().order_by("id"):
        driver = webdriver.WebDriver()
        driver.implicitly_wait(10)
        pattern = brand.product_path
        base_urls = [brand.base_url]
        for b_url in base_urls:
            driver.get(b_url)
            time.sleep(3)
            try:
                driver.find_elements(By.CSS_SELECTOR, "a")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                all_urls = [link.get("href") for link in soup.find_all("a")]
                for url in all_urls:
                    if regex_url(pattern, url):
                        url = url.split("#")[0]
                        base_urls.append(url) if url not in base_urls else None
                        print(url)
                        Formula.objects.get_or_create(
                            brand=Brand.objects.get(english_name=brand.title),
                            product_url=url
                        )
            except Exception as e:
                print(e)
        driver.quit()


def set_base_url_for_crawler():
    with webdriver.WebDriver() as driver:
        driver.maximize_window()
        for selector in ListSelector.objects.filter(base_url=""):
            print(selector.product_path)
            driver.get(selector.product_path.replace("**", ""))
            x = input(f"{selector.title} ")
            selector.base_url = driver.current_url
            selector.save()


def set_title_for_formulas():
    with webdriver.WebDriver() as driver:
        driver.maximize_window()
        driver.implicitly_wait(10)
        for formula in Formula.objects.filter(title="").order_by("brand_id"):
            try:
                driver.get(url=formula.product_url)
                title: str = driver.find_element(By.CSS_SELECTOR, "h1").text.replace("\\n", " ")
                title_str = f'{title.replace("&nbsp", " ").strip()} | {formula.brand.english_name}'
                if "403 Forbidden" in title:
                    raise Exception("403 Forbidden")
                elif "410 Gone" in title:
                    raise Exception("410 Gone")
                elif "찾을 수 없음" in title or "not found" in title or "404" in title:
                    raise Exception("No Product")
                elif Formula.objects.filter(title=title).exists():
                    raise Exception("Already Exist")
                formula.title = title_str
                print(formula.title)
                formula.save()
            except Exception as e:
                if e.__class__.__name__ == "Exception":
                    print(f"[ERROR] {e}", formula.product_url)
                else:
                    print(f"[ERROR] {e.__class__.__name__}", formula.product_url)


def set_selector_for_formula():
    with webdriver.WebDriver() as driver:
        driver.implicitly_wait(10)
        for brand in ListSelector.objects.filter(ingredients_selector=""):
            driver.get(brand.base_url)
            ingredient = input(f"{brand.title} ingredients path.").strip()
            brand.ingredients_selector = ingredient
            brand.save()


def set_ingredients_for_all():
    pass_list = []
    with webdriver.WebDriver() as driver:
        driver.implicitly_wait(10)
        driver.maximize_window()
        for formula in Formula.objects.filter(Q(ingredients=None) | Q(ingredients="")).order_by("brand"):
            try:
                if formula.brand in pass_list:
                    continue
                driver.get(formula.product_url)
                selector = ListSelector.objects.get(brand=formula.brand)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                new_ingredients_selector = input().strip()
                if new_ingredients_selector == "delete":
                    formula.delete()
                    continue
                elif new_ingredients_selector == "pass":
                    pass_list.append(formula.brand)
                    continue
                elif new_ingredients_selector.startswith("/"):
                    formula.ingredients = new_ingredients_selector[1:]
                    formula.save()
                    continue
                elif new_ingredients_selector:
                    selector.ingredients_selector = new_ingredients_selector
                    selector.save()
                ingredients = soup.select(selector.ingredients_selector)
                ingredients = [ingredient.text.strip() for ingredient in ingredients]
                ingredient = ", ".join(ingredients)
                ingredient = re.sub(r"\s+", " ", ingredient.strip())
                ingredient = re.sub("(composition|ingredients?):? ?", "", ingredient, flags=re.IGNORECASE)
                formula.ingredients = ingredient
                print(formula.ingredients)
                formula.save()
            except Exception as e:
                print(f"[ERROR] {e}", formula.product_url)


if __name__ == '__main__':
    set_ingredients_for_all()
