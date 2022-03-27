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

from catfood.models import NaverProduct, ShoppingMall, Brand, Maker
from django.db.utils import IntegrityError

PRODUCT_TYPE = {
    '1': "일반상품",
    '2': "일반상품",
    '3': "일반상품",
    '4': "중고상품",
    '5': "중고상품",
    '6': "중고상품",
    '7': "단종상품",
    '8': "단종상품",
    '9': "단종상품",
    '10': "예정상품",
    '11': "예정상품",
    '12': "예정상품",
}


def naver_shopping_search():
    keywords = [brand.name for brand in Brand.objects.all()]
    DISPLAY_COUNT = 100
    for keyword in keywords:
        start = 1
        while True:
            encText = quote("고양이 " + keyword + " 사료")
            url = f"https://openapi.naver.com/v1/search/shop?query={encText}&display={DISPLAY_COUNT}&start={start}"
            headers = {
                "X-Naver-Client-Id": settings.NAVER_ID,
                "X-Naver-Client-Secret": settings.NAVER_SECRET
            }
            response = requests.get(url, headers=headers)
            if start > 900:
                break
            start += DISPLAY_COUNT
            body = response.json()
            for data in body["items"]:
                print(data)
                if data['category3'] == "고양이 사료":
                    naver_product = NaverProduct.objects.get_or_create(
                        product_id=data['productId'],
                    )[0]  # '11858083484'
                    _title = re.sub("</*b>", "", data['title'])
                    naver_product.title = re.sub(r"[\[(]+\W+[])]+", "", _title)
                    naver_product.link = data['link']
                    naver_product.image_url = data['image']
                    naver_product.low_price = data['lprice']  # '5690'
                    if data['brand']:  # '캐츠랑'
                        brand = Brand.objects.get_or_create(name=data['brand'])[0]
                        naver_product.brand = brand
                    if data['maker']:  # '대주산업'
                        maker = Maker.objects.get_or_create(name=data['maker'])[0]
                        if naver_product.brand:
                            naver_product.brand.maker = maker
                            naver_product.brand.save()
                    if data["mallName"]:
                        naver_product.shopping_mall = ShoppingMall.objects.get_or_create(name=data['mallName'])[0]  # '네이버'
                    naver_product.product_status = PRODUCT_TYPE[data['productType']]  # '1' - 가격 비교 상품
                    naver_product.product_type = data['category4']  # '건식사료'
                    naver_product.save()
            print(start)


if __name__ == '__main__':
    naver_shopping_search()
