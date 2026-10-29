from io import BytesIO
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import FavoriteBrand

PASSWORD = "kopi-susu-2024"


def make_user(email="buyer@ui.ac.id", **extra):
    return User.objects.create_user(username=email, email=email, password=PASSWORD, **extra)


class RegisterLoginTest(TestCase):
    def test_register_creates_user_with_role(self):
        response = self.client.post(reverse("accounts:register"), {
            "full_name": "John PBP", "email": "John@ui.ac.id", "role": "seller", "password": PASSWORD,
        })

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="john@ui.ac.id")
        self.assertEqual(user.profile.role, "seller")
        self.assertFalse(user.profile.is_verified)

    def test_register_rejects_non_ui_email(self):
        response = self.client.post(reverse("accounts:register"), {
            "full_name": "John", "email": "john@gmail.com", "role": "buyer", "password": PASSWORD,
        })

        self.assertContains(response, "Email wajib berakhiran @ui.ac.id.")
        self.assertFalse(User.objects.exists())

    def test_login_with_incomplete_profile_goes_to_edit_profile(self):
        make_user()
        response = self.client.post(reverse("accounts:login"), {"email": "buyer@ui.ac.id", "password": PASSWORD})
        self.assertRedirects(response, reverse("accounts:edit_profile"))

    def test_blocked_user_cannot_login(self):
        make_user(is_active=False)
        response = self.client.post(reverse("accounts:login"), {"email": "buyer@ui.ac.id", "password": PASSWORD})
        self.assertContains(response, "dinonaktifkan")

    def test_sso_login_verifies_account(self):
        xml = (b'<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationSuccess>'
               b'<cas:user>jane.doe</cas:user><cas:attributes><cas:nama>Jane Doe</cas:nama></cas:attributes>'
               b'</cas:authenticationSuccess></cas:serviceResponse>')
        with mock.patch("accounts.views.urlopen", return_value=BytesIO(xml)):
            self.client.get(reverse("accounts:sso_login"), {"ticket": "ST-1"})

        user = User.objects.get(username="jane.doe@ui.ac.id")
        self.assertEqual(user.first_name, "Jane Doe")
        self.assertTrue(user.profile.is_verified)


class ProfileTest(TestCase):
    def setUp(self):
        self.user = make_user(first_name="Buyer")
        self.client.login(username="buyer@ui.ac.id", password=PASSWORD)

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

    def test_profile_shows_verification_status(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertContains(response, "Menunggu verifikasi admin")

    def test_edit_profile(self):
        response = self.client.post(reverse("accounts:edit_profile"), {
            "display_name": "Buy", "faculty": "FASILKOM", "batch": 2024,
            "phone": "081234567890", "photo_url": "", "cod_point": "kutek",
        })

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_complete)
        self.assertIn(("Profil lengkap", "green"), self.user.profile.badges)

    def test_favorite_brand_gives_recommendations(self):
        self.client.post(reverse("accounts:add_favorite_brand"), {"brand": "Uniqlo"})
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "Kemeja linen oversize")

    def test_remove_favorite_brand(self):
        favorite = FavoriteBrand.objects.create(user=self.user, brand="Zara")
        self.client.post(reverse("accounts:remove_favorite_brand", args=[favorite.pk]))
        self.assertFalse(FavoriteBrand.objects.exists())

    def test_cannot_remove_someone_elses_brand(self):
        favorite = FavoriteBrand.objects.create(user=make_user("other@ui.ac.id"), brand="Zara")
        response = self.client.post(reverse("accounts:remove_favorite_brand", args=[favorite.pk]))
        self.assertEqual(response.status_code, 404)

    def test_change_password(self):
        new_password = "teh-manis-2025"
        self.client.post(reverse("accounts:change_password"), {
            "old_password": PASSWORD, "new_password1": new_password, "new_password2": new_password,
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_deactivate_account(self):
        self.client.post(reverse("accounts:close_account"), {"action": "deactivate"})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_delete_account(self):
        self.client.post(reverse("accounts:close_account"), {"action": "delete"})
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())


class StaffTest(TestCase):
    def setUp(self):
        self.admin = make_user("admin@ui.ac.id", is_staff=True)
        self.member = make_user("member@ui.ac.id")
        self.client.login(username="admin@ui.ac.id", password=PASSWORD)

    def test_non_admin_is_forbidden(self):
        self.client.login(username="member@ui.ac.id", password=PASSWORD)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_user_list_filters_by_status(self):
        response = self.client.get(reverse("accounts:user_list"), {"status": "unverified", "q": "member"})
        self.assertContains(response, "member@ui.ac.id")
        self.assertNotContains(response, "admin@ui.ac.id")

    def test_create_admin_account(self):
        self.client.post(reverse("accounts:user_create"), {
            "full_name": "New Admin", "email": "new@ui.ac.id", "role": "buyer",
            "password": PASSWORD, "is_staff": "on", "is_verified": "on",
        })
        user = User.objects.get(username="new@ui.ac.id")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.profile.is_verified)

    def test_edit_user_role_and_verification(self):
        response = self.client.post(reverse("accounts:user_edit", args=[self.member.pk]), {
            "user-first_name": "Member", "user-email": "member@ui.ac.id", "user-is_active": "on",
            "profile-role": "seller", "profile-is_verified": "on",
        })

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.role, "seller")
        self.assertTrue(self.member.profile.is_verified)

    def test_admin_cannot_demote_self(self):
        response = self.client.post(reverse("accounts:user_edit", args=[self.admin.pk]), {
            "user-first_name": "", "user-email": "admin@ui.ac.id", "user-is_active": "on",
            "profile-role": "buyer",
        })
        self.assertContains(response, "tidak bisa mencabut status admin")

    def test_block_and_delete_user(self):
        self.client.post(reverse("accounts:user_toggle_active", args=[self.member.pk]))
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

        self.client.post(reverse("accounts:user_delete", args=[self.member.pk]))
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())

    def test_admin_cannot_delete_self(self):
        response = self.client.post(reverse("accounts:user_delete", args=[self.admin.pk]))
        self.assertEqual(response.status_code, 403)
