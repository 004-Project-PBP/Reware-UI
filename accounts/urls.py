from django.urls import path

from accounts import staff_views, views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("sso/", views.sso_login, name="sso_login"),

    path("profile/", views.show_profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/password/", views.change_password, name="change_password"),
    path("profile/brands/add/", views.add_favorite_brand, name="add_favorite_brand"),
    path("profile/brands/<int:pk>/delete/", views.remove_favorite_brand, name="remove_favorite_brand"),
    path("profile/close/", views.close_account, name="close_account"),

    path("manage/users/", staff_views.user_list, name="user_list"),
    path("manage/users/new/", staff_views.user_create, name="user_create"),
    path("manage/users/<int:pk>/", staff_views.user_edit, name="user_edit"),
    path("manage/users/<int:pk>/toggle-active/", staff_views.user_toggle_active, name="user_toggle_active"),
    path("manage/users/<int:pk>/delete/", staff_views.user_delete, name="user_delete"),
]
