# -*- coding: utf-8 -*-
import os
import re
import sys
from urllib.parse import quote

import requests

sys.path.append('/home/ubuntu/django_catfood')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_catfood.settings")
import django
from django_catfood import settings

if 'setup' in dir(django):
    django.setup()

from catfood.models import NaverProduct, ShoppingMall, Brand


def naver_shopping_search():
    PRODUCT_TYPE = {
        '1':  "일반상품", '2':  "일반상품", '3':  "일반상품",
        '4':  "중고상품", '5':  "중고상품", '6':  "중고상품",
        '7':  "단종상품", '8':  "단종상품", '9':  "단종상품",
        '10': "예정상품", '11': "예정상품", '12': "예정상품",
    }
    DISPLAY_COUNT = 100
    brand_list = [brand for brand in Brand.objects.all() if NaverProduct.objects.filter(brand=brand).count() == 0]

    for brand in brand_list:
        start = 1
        while True:
            encText = quote("고양이 " + brand.korean_name + " 사료")
            url = f"https://openapi.naver.com/v1/search/shop?query={encText}&display={DISPLAY_COUNT}&start={start}"
            headers = {
                "X-Naver-Client-Id": settings.NAVER_ID,
                "X-Naver-Client-Secret": settings.NAVER_SECRET
            }
            response = requests.get(url, headers=headers)
            start += DISPLAY_COUNT
            body = response.json()
            if start > 600 or not len(body.get("items")):
                break
            for data in body["items"]:
                if data['category3'] == "고양이 사료":
                    _title = re.sub("</*b>", "", data['title'])
                    _title = re.sub(r"[\[(]+\W+[])]+", "", _title)
                    if brand.korean_name in _title:
                        print(data)
                        naver_product = NaverProduct.objects.get_or_create(
                            product_id=data['productId'],
                        )[0]  # '11858083484'
                        _title = re.sub("</*b>", "", data['title'])
                        naver_product.title = re.sub(r"[\[(]+\W+[])]+", "", _title)
                        naver_product.link = data['link']
                        naver_product.image_url = data['image']
                        naver_product.low_price = data['lprice']  # '5690'
                        naver_product.brand = brand
                        if data["mallName"]:
                            naver_product.shopping_mall = ShoppingMall.objects.get_or_create(name=data['mallName'])[
                                0]  # '네이버'
                        naver_product.product_status = PRODUCT_TYPE[data['productType']]  # '1' - 가격 비교 상품
                        naver_product.product_type = data['category4']  # '건식사료'
                        naver_product.save()
            print(start)


def extract_brand():
    keywords = dict()
    for product in NaverProduct.objects.all():
        keyword_list = product.title.split()
        if keyword_list[0] in keywords.keys():
            keywords[keyword_list[0]] += 1
        else:
            keywords[keyword_list[0]] = 1
    keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    keywords = [keyword[0] for keyword in keywords if keyword[1] == 1]
    print(keywords)
    with open('exclude.csv', 'w', encoding='utf-8', newline="") as f:
        for keyword in keywords:
            f.write(f'"{keyword}", ""\n')


def not_related_product():
    keywords = ["강아지", "화장실", "모래", "개사료", "하우스", "배변", "낚시대", "장난감", "츄르", "간식", "산책"]
    for product in NaverProduct.objects.all():
        if any(keyword in product.title for keyword in keywords):
            print(product.title)
            product.delete()
        elif not product.product_type:
            print(product.title)
            product.delete()


def find_brand():
    for BRAND in Brand.objects.all():
        NaverProduct.objects.filter(brand=None, title__contains=BRAND.korean_name).update(brand=BRAND)
    BRAND_LIST = [brand.korean_name for brand in Brand.objects.all()]
    for BRAND in BRAND_LIST:
        print(BRAND)
    for product in NaverProduct.objects.filter(brand=None):
        brand = product.title.split()
        if any(brand) in BRAND_LIST:
            for b in brand:
                if b in BRAND_LIST:
                    product.brand = Brand.objects.get(korean_name=b)
                    product.save()
                    break
            print(product.title, True)
        else:
            print(product.title, False)


def main():
    Brand.objects.all().update(is_available=True)
    for brand in Brand.objects.all():
        count = NaverProduct.objects.filter(brand=brand).count()
        if count == 0:
            brand.is_available = False
            brand.save()
            print(f"'{brand}',")


if __name__ == '__main__':
    naver_shopping_search()
    main()
