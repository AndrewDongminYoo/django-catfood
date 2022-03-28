from django.db import models

# Create your models here.


class ProductType(models.TextChoices):
    DRY = '건식사료', 'Dry'
    WET = '습식사료', 'Wet'
    FROZEN_DRY = '동결건조 사료', 'Frozen-Dry'


class ProductStatus(models.TextChoices):
    NORMAL = '일반상품', 'Normal'
    USED = '중고상품', 'Used'
    SOLD_OUT = '단종상품', 'Sold Out'
    BOOKABLE = '예정상품', 'Bookable'


class ShoppingMall(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Maker(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=50)
    maker = models.ForeignKey(Maker, null=True, blank=True, on_delete=models.CASCADE, verbose_name='제조사')

    def __str__(self):
        return self.name


class NaverProduct(models.Model):
    product_id = models.IntegerField(verbose_name='상품 ID')
    title = models.CharField(max_length=100, verbose_name='상품명')
    link = models.URLField(verbose_name='상품 URL')
    image_url = models.URLField(verbose_name='상품 이미지 URL')
    low_price = models.IntegerField(null=True, blank=True, verbose_name='상품 할인가')
    shopping_mall = models.ForeignKey(ShoppingMall, null=True, blank=True, on_delete=models.CASCADE, verbose_name='판매사명')
    product_status = models.CharField(max_length=100, choices=ProductStatus.choices, verbose_name='상품 상태')
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.CASCADE, verbose_name='브랜드명')
    product_type = models.CharField(max_length=100, verbose_name='타입')
