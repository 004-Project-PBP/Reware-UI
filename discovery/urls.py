from django.urls import path
from . import views

app_name = "discovery"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("kategori/<slug:category_slug>/", views.catalog, name="catalog_category"),
    path("kategori/<slug:category_slug>/<slug:brand_slug>/", views.catalog, name="catalog_brand"),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("pencarian-tersimpan/", views.saved_search_page, name="saved_searches"),
    path("riwayat/", views.history_page, name="history"),
    path("admin/statistik/", views.admin_search_stats, name="admin_stats"),
    path('item/add/', views.propose_item, name='propose_item'),
    # AJAX endpoints
    path("api/katalog/", views.api_catalog, name="api_catalog"),
    path("api/wishlist/toggle/", views.api_wishlist_toggle, name="api_wishlist_toggle"),
    path("api/wishlist/<int:pk>/catatan/", views.api_wishlist_note, name="api_wishlist_note"),
    path("api/simpanan/", views.api_saved_search_create, name="api_saved_search_create"),
    path("api/simpanan/<int:pk>/", views.api_saved_search_update, name="api_saved_search_update"),
    path("api/simpanan/<int:pk>/hapus/", views.api_saved_search_delete, name="api_saved_search_delete"),
    path("api/riwayat/<int:pk>/hapus/", views.api_history_delete, name="api_history_delete"),
    path("api/riwayat/bersihkan/", views.api_history_clear, name="api_history_clear"),
    path("api/kontak-seller/<int:pk>/", views.api_seller_contact, name="api_seller_contact"),
]