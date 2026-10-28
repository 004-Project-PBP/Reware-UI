from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    path("", views.my_listings, name="my_listings"),
    path("new/", views.listing_create, name="create"),
    path("<int:pk>/edit/", views.listing_update, name="update"),
    path("<int:pk>/delete/", views.listing_delete, name="delete"),
    path("<int:pk>/status/", views.listing_set_status, name="set_status"),
]