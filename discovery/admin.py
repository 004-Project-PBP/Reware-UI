from django.contrib import admin
from .models import (BlockedKeyword, Brand, Category, CuratedCollection,
                     CuratedCollectionItem, Item, SavedSearch, SearchHistory, WishlistItem)


class CuratedCollectionItemInline(admin.TabularInline):
    model = CuratedCollectionItem
    extra = 1


@admin.register(CuratedCollection)
class CuratedCollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "active_on_homepage", "updated_at")
    inlines = [CuratedCollectionItemInline]  # ubah isi & urutan koleksi


@admin.register(BlockedKeyword)
class BlockedKeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "reason", "created_at")
    search_fields = ("keyword",)


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Item)
admin.site.register(WishlistItem)
admin.site.register(SavedSearch)
admin.site.register(SearchHistory)