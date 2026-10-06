from django.db import models


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name_es


class Service(models.Model):
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name_es


class GeographicSource(models.Model):
    key = models.SlugField(unique=True)
    origin = models.CharField(max_length=300)
    license = models.CharField(max_length=300)
    version = models.CharField(max_length=64)
    synthetic = models.BooleanField(default=True)
    imported_at = models.DateTimeField(auto_now=True)


class Region(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    source = models.ForeignKey(GeographicSource, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Province(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    source = models.ForeignKey(GeographicSource, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Municipality(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.PROTECT)
    source = models.ForeignKey(GeographicSource, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PostalCode(models.Model):
    code = models.CharField(max_length=5, unique=True)
    municipalities = models.ManyToManyField(Municipality)
    source = models.ForeignKey(GeographicSource, on_delete=models.PROTECT)
    public_safe = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Zone(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT)
    source = models.ForeignKey(GeographicSource, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


from .promotion_models import PromotionProduct, PromotionProductVersion  # noqa: E402,F401
