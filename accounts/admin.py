from django.contrib import admin

from accounts.models import FavoriteBrand, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "is_verified", "faculty", "batch"]
    list_filter = ["role", "is_verified", "faculty"]
    search_fields = ["user__username", "display_name"]


admin.site.register(FavoriteBrand)
