import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import AccountCreateForm, FavoriteBrandForm, ProfileForm
from accounts.models import FavoriteBrand
from main.catalog import items_for_brands


# ---------- Register, login, logout ----------

def register_user(request):
    if request.user.is_authenticated:
        return redirect("main:show_main")

    form = AccountCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect("main:show_main")

    context = {"values": request.POST}

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect_after_login(request, user)

        # authenticate() also returns None for blocked accounts, so tell them apart
        blocked = User.objects.filter(username=email, is_active=False).first()
        if blocked is not None and blocked.check_password(password):
            messages.error(request, "Akun ini sedang dinonaktifkan. Hubungi admin.")
        else:
            messages.error(request, "Email atau password salah.")

    return render(request, "accounts/login.html", context)


def redirect_after_login(request, user):
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)

    # "Login -> Lengkapi profil" from the seller and buyer flows
    if not user.profile.is_complete:
        messages.info(request, "Lengkapi profilmu dulu supaya mudah dihubungi saat COD.")
        return redirect("accounts:edit_profile")
    return redirect("main:show_main")


def logout_user(request):
    if request.method != "POST":
        return redirect("main:show_main")

    via_sso = request.session.get("via_sso", False)
    logout(request)

    # Kalau login lewat SSO, keluar juga dari SSO UI
    if via_sso:
        home = request.build_absolute_uri(reverse("main:show_main"))
        return redirect(f"{SSO_URL}/logout?{urlencode({'url': home})}")
    return redirect("main:show_main")


# ---------- SSO UI ----------

# Alamat server SSO UI (CAS), sama seperti yang dipakai library ristekoss/SSO
SSO_URL = "https://sso.ui.ac.id/cas2"
CAS = "{http://www.yale.edu/tp/cas}"


def sso_login(request):
    # Setelah login di SSO UI, browser kembali ke URL ini dengan ?ticket=...
    service = request.build_absolute_uri(reverse("accounts:sso_login"))
    ticket = request.GET.get("ticket")

    if ticket is None:
        return redirect(f"{SSO_URL}/login?{urlencode({'service': service})}")

    # Tanyakan ke SSO UI siapa pemilik ticket ini
    try:
        response = urlopen(f"{SSO_URL}/serviceValidate?{urlencode({'ticket': ticket, 'service': service})}", timeout=10)
        data = ET.fromstring(response.read())
    except (OSError, ET.ParseError):
        data = None

    username = data.findtext(f".//{CAS}user") if data is not None else None
    if username is None:
        messages.error(request, "Login SSO UI gagal. Silakan coba lagi.")
        return redirect("accounts:login")

    # Username sama dengan akun dari form register, jadi satu orang tetap satu akun
    email = f"{username.lower()}@ui.ac.id"
    user, created = User.objects.get_or_create(username=email, defaults={"email": email})
    if not user.is_active:
        messages.error(request, "Akun ini sedang dinonaktifkan. Hubungi admin.")
        return redirect("accounts:login")
    if created:
        user.set_unusable_password()
    user.first_name = data.findtext(f".//{CAS}nama") or user.first_name
    user.save()

    # SSO UI sudah membuktikan dia mahasiswa UI
    user.profile.is_verified = True
    user.profile.save()

    login(request, user)
    request.session["via_sso"] = True
    return redirect_after_login(request, user)


# ---------- Own profile ----------

@login_required
def show_profile(request):
    favorite_brands = request.user.favorite_brands.all()
    context = {
        "profile": request.user.profile,
        "favorite_brands": favorite_brands,
        "brand_form": FavoriteBrandForm(user=request.user),
        "recommended_items": items_for_brands({favorite.brand for favorite in favorite_brands}),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profil berhasil diperbarui.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile_form.html", {"form": form})


@login_required
def change_password(request):
    # SSO accounts have no password yet, so they set one without the old password
    form_class = PasswordChangeForm if request.user.has_usable_password() else SetPasswordForm
    form = form_class(request.user, request.POST or None)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # stay logged in after the change
        messages.success(request, "Kata sandi berhasil diubah.")
        return redirect("accounts:profile")

    return render(request, "accounts/password_form.html", {"form": form})


@login_required
@require_POST
def add_favorite_brand(request):
    form = FavoriteBrandForm(request.POST, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, f"{form.instance.brand} ditambahkan ke brand favorit.")
    else:
        messages.error(request, "Pilih brand yang belum ada di daftar favoritmu.")
    return redirect("accounts:profile")


@login_required
@require_POST
def remove_favorite_brand(request, pk):
    favorite = get_object_or_404(FavoriteBrand, pk=pk, user=request.user)
    favorite.delete()
    messages.success(request, f"{favorite.brand} dihapus dari brand favorit.")
    return redirect("accounts:profile")


@login_required
def close_account(request):
    if request.method != "POST":
        return render(request, "accounts/close_account.html")

    user = request.user
    logout(request)
    if request.POST.get("action") == "delete":
        user.delete()
        messages.success(request, "Akunmu sudah dihapus.")
    else:
        user.is_active = False
        user.save()
        messages.success(request, "Akunmu sudah dinonaktifkan. Hubungi admin untuk mengaktifkannya lagi.")
    return redirect("main:show_main")
