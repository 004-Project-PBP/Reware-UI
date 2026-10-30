"""Admin pages for managing every account. Admin means a user with is_staff."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import StaffAccountCreateForm, StaffProfileForm, StaffUserForm


STATUS_OPTIONS = [
    ("", "Semua status"),
    ("verified", "Terverifikasi"),
    ("unverified", "Belum terverifikasi"),
    ("blocked", "Diblokir"),
]
STATUS_FILTERS = {
    "verified": {"profile__is_verified": True},
    "unverified": {"profile__is_verified": False},
    "blocked": {"is_active": False},
}


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def get_other_user(request, pk):
    """The account to act on; admins use their own profile page for themselves."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        raise PermissionDenied
    return user


@staff_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    users = User.objects.select_related("profile").order_by("-date_joined")
    if query:
        users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query))
    if status in STATUS_FILTERS:
        users = users.filter(**STATUS_FILTERS[status])

    context = {"users": users, "query": query, "status": status, "status_options": STATUS_OPTIONS}
    return render(request, "accounts/staff/user_list.html", context)


@staff_required
def user_create(request):
    form = StaffAccountCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        messages.success(request, f"Akun {user.email} berhasil dibuat.")
        return redirect("accounts:user_list")

    return render(request, "accounts/staff/user_create.html", {"form": form})


@staff_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    user_form = StaffUserForm(request.POST or None, instance=user, editor=request.user, prefix="user")
    profile_form = StaffProfileForm(request.POST or None, instance=user.profile, prefix="profile")

    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, f"Akun {user.email} berhasil diperbarui.")
        return redirect("accounts:user_list")

    context = {"edited_user": user, "user_form": user_form, "profile_form": profile_form}
    return render(request, "accounts/staff/user_edit.html", context)


@staff_required
@require_POST
def user_toggle_active(request, pk):
    user = get_other_user(request, pk)
    user.is_active = not user.is_active
    user.save()
    state = "diaktifkan kembali" if user.is_active else "diblokir"
    messages.success(request, f"Akun {user.email} {state}.")
    return redirect("accounts:user_list")


@staff_required
def user_delete(request, pk):
    user = get_other_user(request, pk)
    if request.method == "POST":
        user.delete()
        messages.success(request, f"Akun {user.email} dihapus.")
        return redirect("accounts:user_list")

    return render(request, "accounts/staff/user_confirm_delete.html", {"edited_user": user})
