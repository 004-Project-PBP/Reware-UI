from django.contrib import admin
from .models import Brand, Category

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand_type', 'is_verified', 'retail_price_min', 'retail_price_max', 'submitted_by')    
    list_filter = ('is_verified', 'brand_type')
    search_fields = ('name',)
    list_editable = ('is_verified', 'brand_type', 'retail_price_min', 'retail_price_max')