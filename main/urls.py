from django.urls import path
from main.views import show_main
from . import views

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    # module 2 - nuel links
    path('katalog/<int:brand_id>/', views.brand_detail, name='brand_detail'),
    path('katalog/propose/', views.propose_brand, name='propose_brand'),
    path('katalog/<int:brand_id>/edit/', views.edit_proposed_brand, name='edit_proposed_brand'),
    path('katalog/<int:brand_id>/delete/', views.delete_proposed_brand, name='delete_proposed_brand'),
    path('katalog/<int:brand_id>/toggle-follow/', views.toggle_follow_brand, name='toggle_follow_brand'),
    path('brand/', views.brand_directory, name='brand_directory'),
]
