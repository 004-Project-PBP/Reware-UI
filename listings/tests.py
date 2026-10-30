from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse

from .models import Listing
from .forms import ListingForm
from django.utils import timezone
from transaksi.models import StubListing, TitikCOD, TransaksiCOD
from main.models import Brand, Category


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

    def test_retail_price_filled_from_brand_midpoint(self):
        brand = Brand.objects.create(
            name="Uniqlo", retail_price_min=100000, retail_price_max=300000
        )
        listing = make_listing(self.seller, brand=brand, retail_price=None, price=100000)
        self.assertEqual(listing.retail_price, 200000)
        self.assertEqual(listing.savings_percent, 50)

    def test_manual_retail_price_is_not_overridden_by_brand(self):
        brand = Brand.objects.create(
            name="Uniqlo", retail_price_min=100000, retail_price_max=300000
        )
        listing = make_listing(self.seller, brand=brand, retail_price=150000)
        self.assertEqual(listing.retail_price, 150000)
    
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

    def test_form_accepts_brand_and_category(self):
        brand = Brand.objects.create(
            name="Uniqlo", retail_price_min=100000, retail_price_max=300000
        )
        category = Category.objects.create(name="Atasan")
        form = ListingForm(data=form_data(brand=brand.pk, category=category.pk))
        self.assertTrue(form.is_valid())


class ListingViewTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pass12345")
        self.other = User.objects.create_user("other", password="pass12345")
        self.listing = make_listing(self.seller)

    # --- my listings ---
    def test_my_listings_requires_login(self):
        resp = self.client.get(reverse("listings:my_listings"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse(settings.LOGIN_URL), resp["Location"])

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

    def test_my_listings_counts_pending_requests(self):
        titik = TitikCOD.objects.create(
            nama_lokasi="Stasiun UI", latitude="-6.360000", longitude="106.830000"
        )
        stub = StubListing.mirror_of(self.listing)
        TransaksiCOD.objects.create(
            listing=stub, buyer=self.other, seller=self.seller,
            titik_cod=titik, jadwal_temu=timezone.now(),
        )
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:my_listings"))
        self.assertEqual(resp.context["pending_total"], 1)
        self.assertEqual(resp.context["listings"][0].pending_count, 1)

    def test_my_listings_shows_placeholder_without_photo(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:my_listings"))
        self.assertContains(resp, "lp-thumb-empty")

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

        # --- update ---
    def test_update_by_owner(self):
        self.client.login(username="seller", password="pass12345")
        url = reverse("listings:update", args=[self.listing.pk])
        resp = self.client.post(url, form_data(title="Judul Baru"))
        self.assertRedirects(resp, reverse("listings:my_listings"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Judul Baru")

    def test_update_by_other_user_returns_404(self):
        self.client.login(username="other", password="pass12345")
        url = reverse("listings:update", args=[self.listing.pk])
        resp = self.client.post(url, form_data(title="Dibajak"))
        self.assertEqual(resp.status_code, 404)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Uniqlo Tee")

        # --- Delete ---
    def test_delete_by_owner(self):
        self.client.login(username="seller", password="pass12345")
        self.client.post(reverse("listings:delete", args=[self.listing.pk]))
        self.assertFalse(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_delete_by_other_user_returns_404(self):
        self.client.login(username="other", password="pass12345")
        resp = self.client.post(reverse("listings:delete", args=[self.listing.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_delete_rejects_get(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:delete", args=[self.listing.pk]))
        self.assertEqual(resp.status_code, 405)

        # --- status ---
    def test_set_status_valid(self):
        self.client.login(username="seller", password="pass12345")
        url = reverse("listings:set_status", args=[self.listing.pk])
        self.client.post(url, {"status": "sold"})
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.SOLD)

    def test_set_status_invalid_is_ignored(self):
        self.client.login(username="seller", password="pass12345")
        url = reverse("listings:set_status", args=[self.listing.pk])
        self.client.post(url, {"status": "ngawur"})
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.AVAILABLE)

    def test_set_status_by_other_user_returns_404(self):
        self.client.login(username="other", password="pass12345")
        url = reverse("listings:set_status", args=[self.listing.pk])
        resp = self.client.post(url, {"status": "sold"})
        self.assertEqual(resp.status_code, 404)
    
    def test_set_status_ajax_returns_json(self):
        self.client.login(username="seller", password="pass12345")
        url = reverse("listings:set_status", args=[self.listing.pk])
        resp = self.client.post(
            url, {"status": "sold"}, headers={"X-Requested-With": "XMLHttpRequest"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "sold")
        self.assertEqual(data["available"], 0)

    def test_set_status_ajax_invalid_returns_400(self):
        self.client.login(username="seller", password="pass12345")
        url = reverse("listings:set_status", args=[self.listing.pk])
        resp = self.client.post(
            url, {"status": "ngawur"}, headers={"X-Requested-With": "XMLHttpRequest"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])

        # --- detail ---
    def test_detail_guest_hides_private_info(self):
        resp = self.client.get(reverse("listings:detail", args=[self.listing.pk]))
        self.assertContains(resp, "Uniqlo Tee")
        self.assertContains(resp, "Masuk untuk mengajukan beli")
        self.assertNotContains(resp, "Stasiun UI")
        self.assertNotContains(resp, "Ajukan Beli</button>")

    def test_detail_logged_in_buyer_sees_cod_and_buy_button(self):
        self.client.login(username="other", password="pass12345")
        resp = self.client.get(reverse("listings:detail", args=[self.listing.pk]))
        self.assertContains(resp, "Stasiun UI")
        self.assertContains(resp, "Ajukan Beli")

    def test_detail_owner_sees_manage_link(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(reverse("listings:detail", args=[self.listing.pk]))
        self.assertContains(resp, "Kelola listing ini")

    def test_detail_archived_hidden_from_others_but_visible_to_owner(self):
        archived = make_listing(self.seller, status=Listing.Status.ARCHIVED)
        url = reverse("listings:detail", args=[archived.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.login(username="seller", password="pass12345")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_detail_unknown_id_returns_404(self):
        resp = self.client.get(reverse("listings:detail", args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_create_with_brand_autofills_retail_price(self):
        brand = Brand.objects.create(
            name="Uniqlo", retail_price_min=100000, retail_price_max=300000
        )
        self.client.login(username="seller", password="pass12345")
        self.client.post(
            reverse("listings:create"),
            form_data(brand=brand.pk, retail_price="", action="publish"),
        )
        new = Listing.objects.get(title="Item Baru")
        self.assertEqual(new.brand, brand)
        self.assertEqual(new.retail_price, 200000)

    def test_dashboard_and_detail_show_brand_name(self):
        brand = Brand.objects.create(
            name="Zara", retail_price_min=100000, retail_price_max=300000
        )
        self.listing.brand = brand
        self.listing.save()
        self.client.login(username="seller", password="pass12345")
        self.assertContains(self.client.get(reverse("listings:my_listings")), "Zara")
        self.assertContains(
            self.client.get(reverse("listings:detail", args=[self.listing.pk])), "Zara"
        )

    