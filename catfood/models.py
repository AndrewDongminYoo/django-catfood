from django.db import models

# Create your models here.


class NaverProduct(models.Model):
    product_id = models.IntegerField(verbose_name='상품 ID')
    title = models.CharField(max_length=100, verbose_name='상품명')
    link = models.URLField(verbose_name='상품 URL')
    image_url = models.URLField(verbose_name='상품 이미지 URL')
    low_price = models.IntegerField(null=True, blank=True, verbose_name='상품 할인가')
    shopping_mall = models.CharField(max_length=100, verbose_name='쇼핑몰')
    product_type = models.CharField(max_length=100, verbose_name='상품 종류')
    brand = models.CharField(max_length=100, verbose_name='브랜드')
    maker = models.CharField(max_length=100, verbose_name='제조사')
    texture = models.CharField(max_length=100, verbose_name='타입')


class ShoppingMall(models.Model):
    mall_name = models.CharField(max_length=100, verbose_name='쇼핑몰명')
    mall_url = models.URLField(verbose_name='쇼핑몰 URL')


class ProductType(models.Model):
    type_name = models.CharField(max_length=100, verbose_name='상품 종류')


class Brand(models.Model):
    brand_name = models.CharField(max_length=100, verbose_name='브랜드명')

