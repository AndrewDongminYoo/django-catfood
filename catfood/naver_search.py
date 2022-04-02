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
    DISPLAY_COUNT = 100
    brand_list = [brand for brand in Brand.objects.all() if NaverProduct.objects.filter(brand=brand).count() < 20]
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
            if start > 600:
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
                    naver_product.brand = brand if brand.korean_name in naver_product.title else None
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
        # product.title = product.title\
        #     .replace("[", " ")\
        #     .replace("]", " ") \
        #     .replace("{", " ") \
        #     .replace("}", " ") \
        #     .replace("(", " ")\
        #     .replace(")", " ")\
        #     .replace("/", " ")\
        #     .replace("-", " ")\
        #     .replace("+", " ")\
        #     .replace("_", " ")\
        #     .replace("#", " ")\
        #     .replace("!", " ")\
        #     .replace("@", " ")\
        #     .replace("$", " ")\
        #     .replace("*", " ")\
        #     .replace("~", " ")\
        #     .replace(",", " ")\
        #     .replace("&gt", " ")\
        #     .replace("&lt", " ")\
        #     .replace("&amp;", "&")\
        #     .replace("  ", " ")\
        #     .replace("  ", " ")\
        #     .replace("  ", " ")
        # product.save()
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
    keywords = ["강아지", "화장실", "모래", "개사료", "하우스", "배변", "낚시대", "장난감", "진도", "리트리버", "츄르", "간식"]
    for product in NaverProduct.objects.all():
        if any(keyword in product.title for keyword in keywords):
            print(product.title)
            product.delete()
        elif not product.product_type:
            print(product.title)
            product.delete()


def make_word_spaces_for_titles():
    for product in NaverProduct.objects.all():
        product.title = product.title\
            .replace("치킨", " 치킨 ")\
            .replace("닭간", " 닭간 ")\
            .replace("닭고기", " 닭고기 ")\
            .replace("참치", " 참치 ")\
            .replace("연어", " 연어 ")\
            .replace("흰살생선", " 흰살생선 ")\
            .replace("흰생선", " 흰살생선 ")\
            .replace("생선", " 생선 ")\
            .replace("피쉬", " 피쉬 ")\
            .replace("소고기", " 소고기 ")\
            .replace("소간", " 소간 ")\
            .replace("고양이", "")\
            .replace("캣", " 캣 ")\
            .replace("사료", " 사료 ")\
            .replace("  ", " ")\
            .replace("  ", " ")\
            .replace("  ", " ")\
            .replace("& 39;", "'")\
            .strip()
        product.save()


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
        else:
            print(brand, False)


if __name__ == '__main__':
    naver_shopping_search()
    find_brand()
