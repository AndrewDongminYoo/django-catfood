from django.db import models

# Create your models here.


class ProductType(models.TextChoices):
    DRY = '건식사료', 'Dry'
    WET = '습식사료', 'Wet'
    FROZEN_DRY = '동결건조 사료', 'Frozen-Dry'
    MILK = '분유/우유', 'Baby Milk'


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
    country = models.CharField(max_length=50)
    searchable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Brand(models.Model):
    english_name = models.CharField(max_length=50)
    korean_name = models.CharField(max_length=50)
    maker = models.ForeignKey(Maker, null=True, blank=True, on_delete=models.CASCADE, verbose_name='제조사')
    url = models.URLField(null=True, blank=True, verbose_name='사이트 URL')
    is_available = models.BooleanField(default=False, verbose_name='판매 여부')

    def __str__(self):
        return self.korean_name


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


class ListSelector(models.Model):
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.CASCADE, verbose_name='브랜드명')
    base_url = models.URLField(verbose_name='상품 베이스 URL')
    title = models.TextField(verbose_name='상품명 선택자')
    product_path = models.TextField(verbose_name='상품 선택자')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)


class Formula(models.Model):
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.CASCADE, verbose_name='브랜드명')
    title = models.CharField(max_length=200, null=True, blank=True, verbose_name='상품명')
    product_url = models.URLField(verbose_name='상품 URL')
