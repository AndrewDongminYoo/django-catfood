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

PRODUCT_TYPE = {
    '1': "일반 가격비교 상품",
    '2': "일반 가격비교 비매칭 일반상품",
    '3': "일반 가격비교 매칭 일반상품",
    '4': "중고 가격비교 상품",
    '5': "중고 가격비교 비매칭 일반상품",
    '6': "중고 가격비교 매칭 일반상품",
    '7': "단종 가격비교 상품",
    '8': "단종 가격비교 비매칭 일반상품",
    '9': "단종 가격비교 매칭 일반상품",
    '10': "예정 가격비교 상품",
    '11': "예정 가격비교 비매칭 일반상품",
    '12': "예정 가격비교 매칭 일반상품",
}

count = 0
DISPLAY_COUNT = 100

while True:
    encText = quote("고양이 사료")
    url = f"https://openapi.naver.com/v1/search/shop?query={encText}&display={DISPLAY_COUNT}"  # json 결과
    headers = {
        "X-Naver-Client-Id": settings.NAVER_ID,
        "X-Naver-Client-Secret": settings.NAVER_SECRET
    }
    response = requests.get(url, headers=headers)
    code = response.status_code
    count += DISPLAY_COUNT

    if code == 200:
        body = response.json()
        if body["total"] <= count:
            continue
        for data in body["items"]:
            title = re.sub("</*b>", "", data['title'])
            title = re.sub(r"[\[(]+[a-zA-Z가-힣0-9 ]+[])]+", "", title)
            link = data['link']
            image_url = data['image']
            low_price = data['lprice']  # '5690'
            high_price = data['hprice']  # ""
            shopping_mall = data['mallName']  # '네이버'
            product_id = data['productId']  # '11858083484'
            product_type = PRODUCT_TYPE[data['productType']]  # '1' - 가격 비교 상품
            brand = data['brand']  # '캐츠랑'
            maker = data['maker']  # '대주산업'
            category1 = data['category1']  # '생활/건강'
            category2 = data['category2']  # '반려동물'
            category3 = data['category3']  # '고양이 사료'
            category4 = data['category4']  # '건식사료'
            
    else:
        print("Error Code:" + str(code))
