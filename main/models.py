from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True) 

    def __str__(self):
        return self.name

class Brand(models.Model):
    BRAND_TYPES = [
        ('Not Defined', 'Not Defined'),
        ('Lokal', 'Lokal'),
        ('Premium', 'Premium'),
        ('Vintage', 'Vintage'),
    ]

    name = models.CharField(max_length=150, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    brand_type = models.CharField(max_length=50, choices=BRAND_TYPES, default='Not Defined')
    categories = models.ManyToManyField(Category, related_name='brands')
    
    # Retail price in IDR
    retail_price_min = models.PositiveIntegerField(default=0)
    retail_price_max = models.PositiveIntegerField(default=0)
    
    # Verification and track user who proposed it
    is_verified = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    followers = models.ManyToManyField(User, related_name='followed_brands', blank=True)

    def __str__(self):
        return self.name