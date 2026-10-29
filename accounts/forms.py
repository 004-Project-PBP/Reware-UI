from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from accounts.models import FavoriteBrand, Profile


def clean_ui_email(email, current_user=None):
    """Email doubles as the username, so it is stored lowercase and must be unique."""
    email = email.strip().lower()
    if not email.endswith("@ui.ac.id"):
        raise forms.ValidationError("Email wajib berakhiran @ui.ac.id.")
    taken = User.objects.filter(username=email)
    if current_user is not None:
        taken = taken.exclude(pk=current_user.pk)
    if taken.exists():
        raise forms.ValidationError("Email ini sudah terdaftar.")
    return email


class AccountCreateForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=150,
                                widget=forms.TextInput(attrs={"placeholder": "ex. John PBP", "autocomplete": "name"}))
    email = forms.EmailField(label="Email UI Address",
                             widget=forms.EmailInput(attrs={"placeholder": "ex. john.pbp67@ui.ac.id", "autocomplete": "email"}))
    role = forms.ChoiceField(label="Daftar sebagai", choices=Profile.ROLE_CHOICES)
    password = forms.CharField(label="Password",
                               widget=forms.PasswordInput(attrs={"placeholder": "ex. NeverTellAnyoneYourPassword", "autocomplete": "new-password"}))

    def clean_email(self):
        return clean_ui_email(self.cleaned_data["email"])

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            user = User(username=cleaned_data.get("email", ""), first_name=cleaned_data.get("full_name", ""))
            try:
                validate_password(password, user)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, is_staff=False, is_verified=False):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["email"], email=data["email"], password=data["password"],
            first_name=data["full_name"], is_staff=is_staff,
        )
        user.profile.role = data["role"]
        user.profile.is_verified = is_verified
        user.profile.save()
        return user


class StaffAccountCreateForm(AccountCreateForm):
    """Admins create accounts the same way, and can make them admins or verify them right away."""
    is_staff = forms.BooleanField(label="Jadikan admin", required=False)
    is_verified = forms.BooleanField(label="Langsung terverifikasi", required=False)

    def save(self):
        return super().save(is_staff=self.cleaned_data["is_staff"], is_verified=self.cleaned_data["is_verified"])


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "faculty", "batch", "phone", "photo_url", "cod_point"]
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "ex. John"}),
            "batch": forms.NumberInput(attrs={"placeholder": "ex. 2024"}),
            "phone": forms.TextInput(attrs={"placeholder": "ex. 081234567890"}),
            "photo_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }


class FavoriteBrandForm(forms.ModelForm):
    class Meta:
        model = FavoriteBrand
        fields = ["brand"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user
        # Only offer brands the user has not picked yet
        picked = set(user.favorite_brands.values_list("brand", flat=True))
        self.fields["brand"].choices = [
            choice for choice in self.fields["brand"].choices if choice[0] not in picked
        ]


class StaffUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "email", "is_staff", "is_active"]
        labels = {
            "first_name": "Nama lengkap",
            "is_staff": "Admin",
            "is_active": "Aktif (hapus centang untuk memblokir)",
        }

    def __init__(self, *args, editor, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.fields["email"].required = True

    def clean_email(self):
        return clean_ui_email(self.cleaned_data["email"], current_user=self.instance)

    def clean(self):
        cleaned_data = super().clean()
        # Admins cannot lock themselves out
        if self.instance == self.editor and not (cleaned_data.get("is_staff") and cleaned_data.get("is_active")):
            raise forms.ValidationError("Kamu tidak bisa mencabut status admin atau memblokir akunmu sendiri.")
        return cleaned_data

    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        return super().save(commit)


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["role", "is_verified", "display_name", "faculty", "batch", "phone", "cod_point"]
