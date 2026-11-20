from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api import ListingViewSet

app_name = "listings"

router = DefaultRouter()
router.register("listings", ListingViewSet, basename="listing")

urlpatterns = [
    path("", views.my_listings, name="my_listings"),
    path("new/", views.listing_create, name="create"),
    path("<int:pk>/edit/", views.listing_update, name="update"),
    path("<int:pk>/delete/", views.listing_delete, name="delete"),
    path("<int:pk>/status/", views.listing_set_status, name="set_status"),
    path("<int:pk>/", views.listing_detail, name="detail"),
    path("api/", include(router.urls)),
]