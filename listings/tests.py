from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse

from .models import Listing
from .forms import ListingForm


User = get_user_model()


def make_listing(seller, **kwargs):
    data = dict(
        title="Uniqlo Tee", description="Masih bagus", size="M",
        condition="good", price=50000, retail_price=100000,
        stock=1, cod_point="Stasiun UI",
    )
    data.update(kwargs)
    return Listing.objects.create(seller=seller, **data)


class ListingModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pass12345")

    def test_str_returns_title(self):
        self.assertEqual(str(make_listing(self.seller)), "Uniqlo Tee")

    def test_default_status_is_available(self):
        self.assertEqual(make_listing(self.seller).status, Listing.Status.AVAILABLE)

    def test_savings_percent_is_calculated(self):
        listing = make_listing(self.seller, price=50000, retail_price=70000)
        self.assertEqual(listing.savings_percent, 29)

    def test_savings_percent_none_without_retail_price(self):
        listing = make_listing(self.seller, retail_price=None)
        self.assertIsNone(listing.savings_percent)

    def test_savings_percent_none_when_retail_not_higher(self):
        same = make_listing(self.seller, price=50000, retail_price=50000)
        lower = make_listing(self.seller, price=50000, retail_price=40000)
        self.assertIsNone(same.savings_percent)
        self.assertIsNone(lower.savings_percent)
    
def form_data(**kwargs):
    data = {
        "title": "Item Baru", "description": "Deskripsi", "size": "M",
        "condition": "good", "price": "50000", "retail_price": "100000",
        "stock": "1", "cod_point": "Stasiun UI",
    }
    data.update(kwargs)
    return data


class ListingFormTests(TestCase):
    def test_valid_form(self):
        self.assertTrue(ListingForm(data=form_data()).is_valid())

    def test_price_zero_is_invalid(self):
        form = ListingForm(data=form_data(price="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_title_is_required(self):
        form = ListingForm(data=form_data(title=""))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class ListingViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pass12345")
        self.other = User.objects.create_user("other", password="pass12345")
        self.listing = make_listing(self.seller)

    # --- my listings ---
    def test_my_listings_requires_login(self):
        resp = self.client.get(reverse("listings:my_listings"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(settings.LOGIN_URL, resp["Location"])

    def test_my_listings_shows_only_own_items(self):
        make_listing(self.other, title="Punya Orang Lain")
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:my_listings"))
        self.assertContains(resp, "Uniqlo Tee")
        self.assertNotContains(resp, "Punya Orang Lain")

    def test_my_listings_status_filter(self):
        make_listing(self.seller, title="Item Arsip", status=Listing.Status.ARCHIVED)
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:my_listings") + "?status=available")
        self.assertContains(resp, "Uniqlo Tee")
        self.assertNotContains(resp, "Item Arsip")

    # --- create ---
    def test_create_requires_login(self):
        resp = self.client.post(reverse("listings:create"), form_data())
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Listing.objects.count(), 1)

    def test_create_publish_sets_seller_and_available(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.post(reverse("listings:create"), form_data(action="publish"))
        self.assertRedirects(resp, reverse("listings:my_listings"))
        new = Listing.objects.get(title="Item Baru")
        self.assertEqual(new.seller, self.seller)
        self.assertEqual(new.status, Listing.Status.AVAILABLE)

    def test_create_draft_is_archived(self):
        self.client.login(username="seller", password="pass12345")
        self.client.post(reverse("listings:create"), form_data(action="draft"))
        self.assertEqual(
            Listing.objects.get(title="Item Baru").status, Listing.Status.ARCHIVED
        )

    def test_create_invalid_price_is_not_saved(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.post(reverse("listings:create"), form_data(price="0"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Listing.objects.count(), 1)