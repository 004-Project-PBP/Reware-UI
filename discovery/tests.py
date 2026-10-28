from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import (BlockedKeyword, Brand, Category, CuratedCollection,
                     CuratedCollectionItem, Item, SavedSearch, SearchHistory,
                     WishlistItem)

User = get_user_model()


class DiscoveryDataMixin:
    """Small deterministic catalog: 1 seller, 1 buyer, 1 staff, 2 items."""

    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user("seller", password="x")
        cls.buyer = User.objects.create_user("buyer", password="x")
        cls.staff = User.objects.create_user("staff", password="x", is_staff=True)

        cls.atasan = Category.objects.create(name="Atasan")
        cls.bawahan = Category.objects.create(name="Bawahan")
        cls.uniqlo = Brand.objects.create(name="Uniqlo")
        cls.uniqlo.categories.add(cls.atasan)

        cls.item = Item.objects.create(
            name="Kemeja linen oversize", category=cls.atasan, brand=cls.uniqlo,
            seller=cls.seller, price=85000, retail_price=283000,
            size="L", condition="seperti_baru", cod_location="Balairung")
        cls.item2 = Item.objects.create(
            name="Celana chino slim", category=cls.bawahan, brand=cls.uniqlo,
            seller=cls.seller, price=95000, size="32", cod_location="Balairung")

    def render(self, template, context=None, user=None):
        """Render a template with a request bound to `user` (or anonymous)."""
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        return render_to_string(template, context or {}, request=request)


class TemplateCompileTests(TestCase):
    """Smoke test: every template must at least load (catches syntax errors)."""

    TEMPLATES = [
        "discovery/base.html",
        "discovery/catalog.html",
        "discovery/partials/item_grid.html",
        "discovery/wishlist.html",
        "discovery/saved_searches.html",
        "discovery/history.html",
        "discovery/admin_stats.html",
        "discovery/partials/curation_home.html",
    ]

    def test_templates_compile(self):
        for name in self.TEMPLATES:
            with self.subTest(template=name):
                get_template(name)


class BaseTemplateTests(DiscoveryDataMixin, TestCase):
    """discovery/base.html — shell, topbar, wishlist counter."""

    def test_anonymous_topbar(self):
        html = self.render("discovery/base.html")
        self.assertIn("dshell__topbar", html)
        self.assertIn("Masuk", html)
        self.assertNotIn("Wishlist (", html)

    def test_authenticated_topbar_shows_live_count(self):
        WishlistItem.objects.create(buyer=self.buyer, item=self.item)
        html = self.render("discovery/base.html", user=self.buyer)
        self.assertIn('id="wishlist-count">1</span>', html)
        self.assertIn(reverse("discovery:saved_searches"), html)

    def test_loads_discovery_js(self):
        html = self.render("discovery/base.html")
        self.assertIn("discovery/js/discovery.js", html)


class CatalogTemplateTests(DiscoveryDataMixin, TestCase):
    """discovery/catalog.html — hierarchy, filter form, states."""

    def test_root_level_shows_categories_and_filter_form(self):
        res = self.client.get(reverse("discovery:catalog"))
        self.assertTemplateUsed(res, "discovery/catalog.html")
        self.assertContains(res, "Atasan")
        self.assertContains(res, "Bawahan")
        self.assertContains(res, 'id="filter-form"')
        self.assertContains(res, 'id="item-grid"')
        self.assertContains(res, 'id="load-more"')
        self.assertContains(res, "item ditemukan")
        # filter controls
        for label in ("Ukuran", "Kondisi", "Titik COD", "Harga jual", "Terbaru"):
            self.assertContains(res, label)

    def test_category_level_shows_brand_chips(self):
        res = self.client.get(reverse("discovery:catalog_category", args=[self.atasan.slug]))
        self.assertContains(res, "Uniqlo")

    def test_brand_level_renders_item_cards(self):
        res = self.client.get(reverse("discovery:catalog_brand",
                                      args=[self.atasan.slug, self.uniqlo.slug]))
        self.assertContains(res, "Kemeja linen oversize")
        self.assertContains(res, "Rp85.000")
        self.assertContains(res, "Hemat 70%")

    def test_no_match_shows_empty_state(self):
        res = self.client.get(reverse("discovery:catalog"), {"q": "zzz-tidak-ada"})
        self.assertContains(res, "Tidak ada item yang cocok dengan filter.")

    def test_blocked_keyword_message(self):
        BlockedKeyword.objects.create(keyword="terlarang")
        res = self.client.get(reverse("discovery:catalog"), {"q": "terlarang"})
        self.assertContains(res, "diblokir admin")


class ItemGridPartialTests(DiscoveryDataMixin, TestCase):
    """discovery/partials/item_grid.html — cards, heart state, AJAX reuse."""

    def test_card_content(self):
        html = render_to_string("discovery/partials/item_grid.html",
                                {"items": [self.item], "wishlist_ids": set()})
       