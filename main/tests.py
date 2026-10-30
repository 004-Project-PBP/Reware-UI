from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from listings.models import Listing

from .forms import BrandProposalForm
from .models import Brand, Category


def make_brand(name, brand_type="Fast Fashion", low=100000, high=300000,
               categories=(), **kwargs):
    brand = Brand.objects.create(
        name=name, brand_type=brand_type,
        retail_price_min=low, retail_price_max=high, **kwargs,
    )
    brand.categories.set(categories)
    return brand


def make_listing(seller, brand, price=100000, **kwargs):
    return Listing.objects.create(
        seller=seller, brand=brand, title="Item", price=price,
        cod_point="Stasiun UI", **kwargs,
    )


def proposal_data(categories, **kwargs):
    data = {
        "name": "Pull&Bear", "logo_url": "", "brand_type": "Lokal",
        "categories": [c.pk for c in categories],
        "retail_price_min": "100000", "retail_price_max": "400000",
    }
    data.update(kwargs)
    return data


class BrandModelTests(TestCase):
    def test_str_returns_name(self):
        self.assertEqual(str(make_brand("Uniqlo")), "Uniqlo")


class BrandFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Atasan")

    def test_valid_form(self):
        form = BrandProposalForm(data=proposal_data([self.category]))
        self.assertTrue(form.is_valid(), form.errors)

    def test_min_price_above_max_is_invalid(self):
        form = BrandProposalForm(data=proposal_data(
            [self.category], retail_price_min="500000", retail_price_max="100000"
        ))
        self.assertFalse(form.is_valid())

    def test_category_is_required(self):
        form = BrandProposalForm(data=proposal_data([]))
        self.assertFalse(form.is_valid())
        self.assertIn("categories", form.errors)


class HomeAndDirectoryTests(TestCase):
    def setUp(self):
        atasan = Category.objects.create(name="Atasan")
        sepatu = Category.objects.create(name="Sepatu")
        self.uniqlo = make_brand("Uniqlo", "Fast Fashion", 100000, 450000, [atasan])
        self.erigo = make_brand("Erigo", "Lokal", 89000, 350000, [atasan])
        self.nike = make_brand("Nike", "Premium", 300000, 1500000, [sepatu])

    def names(self, **params):
        resp = self.client.get(reverse("main:brand_directory"), params)
        self.assertEqual(resp.status_code, 200)
        return {b.name for b in resp.context["brands"]}

    def test_home_page_loads(self):
        self.assertEqual(self.client.get(reverse("main:show_main")).status_code, 200)

    def test_directory_lists_all_brands(self):
        self.assertEqual(self.names(), {"Uniqlo", "Erigo", "Nike"})

    def test_directory_search_by_name(self):
        self.assertEqual(self.names(q="uni"), {"Uniqlo"})

    def test_directory_filter_by_category(self):
        self.assertEqual(self.names(category="Sepatu"), {"Nike"})

    def test_directory_filter_by_brand_type(self):
        self.assertEqual(self.names(brand_type="Lokal"), {"Erigo"})

    def test_directory_filter_by_max_price(self):
        self.assertEqual(self.names(max_price="400000"), {"Erigo"})

    def test_directory_counts_only_available_listings(self):
        seller = User.objects.create_user("seller", password="pass12345")
        make_listing(seller, self.uniqlo)
        make_listing(seller, self.uniqlo)
        make_listing(seller, self.uniqlo, status=Listing.Status.SOLD)
        resp = self.client.get(reverse("main:brand_directory"))
        counts = {b.name: b.active_listings_count for b in resp.context["brands"]}
        self.assertEqual(counts["Uniqlo"], 2)
        self.assertEqual(counts["Erigo"], 0)

class BrandDetailTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pass12345")
        self.brand = make_brand("Uniqlo", low=100000, high=300000)
        make_listing(self.seller, self.brand, price=100000)
        make_listing(self.seller, self.brand, price=60000)
        make_listing(self.seller, self.brand, price=10000, status=Listing.Status.SOLD)
        self.url = reverse("main:brand_detail", args=[self.brand.pk])

    def test_guest_sees_locked_stats(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Statistik Detail Brand Dikunci")
        self.assertEqual(resp.context["avg_thrift_price"], 0)

    def test_logged_in_sees_stats(self):
        self.client.login(username="seller", password="pass12345")
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["active_listings_count"], 2)
        self.assertEqual(resp.context["avg_thrift_price"], 80000)
        self.assertEqual(resp.context["avg_savings_pct"], 60)

    def test_only_available_listings_shown(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["listings"].count(), 2)

    def test_unknown_brand_returns_404(self):
        resp = self.client.get(reverse("main:brand_detail", args=[9999]))
        self.assertEqual(resp.status_code, 404)