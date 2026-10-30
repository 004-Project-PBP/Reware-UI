from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from listings.models import Listing

from .models import StubListing, TitikCOD, TransaksiCOD
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import StubListing, TitikCOD, TransaksiCOD, Ulasan


User = get_user_model()



class ListingToTransaksiFlowTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="pw12345!")
        self.buyer = User.objects.create_user("buyer", password="pw12345!")
        self.listing = Listing.objects.create(
            seller=self.seller, title="Jaket denim", price=90000,
            retail_price=300000, cod_point="Stasiun UI",
        )
        self.titik = TitikCOD.objects.create(
            nama_lokasi="Stasiun UI", latitude=-6.36, longitude=106.83
        )

    def test_listing_detail_links_to_purchase_flow(self):
        self.client.force_login(self.buyer)
        resp = self.client.get(reverse("listings:detail", args=[self.listing.pk]))
        self.assertContains(
            resp, reverse("transaksi:ajukan_dari_listing", args=[self.listing.pk])
        )

    def test_ajukan_dari_listing_requires_login(self):
        url = reverse("transaksi:ajukan_dari_listing", args=[self.listing.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_ajukan_dari_listing_mirrors_and_redirects_to_form(self):
        self.client.force_login(self.buyer)
        resp = self.client.get(
            reverse("transaksi:ajukan_dari_listing", args=[self.listing.pk])
        )
        stub = StubListing.objects.get(source=self.listing)
        self.assertRedirects(
            resp, reverse("transaksi:ajukan_beli", args=[stub.id]),
        )
        self.assertEqual(stub.selling_price, 90000)
        self.assertEqual(stub.seller, self.seller)

    def test_archived_listing_cannot_be_requested(self):
        self.listing.status = Listing.Status.ARCHIVED
        self.listing.save()
        self.client.force_login(self.buyer)
        resp = self.client.get(
            reverse("transaksi:ajukan_dari_listing", args=[self.listing.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_approve_and_complete_sync_listing_status(self):
        stub = StubListing.mirror_of(self.listing)
        titik = self.titik
        trx = TransaksiCOD.objects.create(
            listing=stub, buyer=self.buyer, seller=self.seller, titik_cod=titik,
            jadwal_temu=timezone.now() + timedelta(days=1),
        )
        self.client.force_login(self.seller)
        self.client.post(
            reverse("transaksi:respon_pengajuan_ajax", args=[trx.id]),
            {"aksi": "setujui"},
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.BOOKED)

        self.client.post(reverse("transaksi:selesaikan_transaksi", args=[trx.id]))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.SOLD)

    def test_detail_transaksi_renders_for_participants(self):
        stub = StubListing.mirror_of(self.listing)
        trx = TransaksiCOD.objects.create(
            listing=stub, buyer=self.buyer, seller=self.seller,
            titik_cod=self.titik,
            jadwal_temu=timezone.now() + timedelta(days=1),
        )
        self.client.force_login(self.buyer)
        resp = self.client.get(reverse("transaksi:detail_transaksi", args=[trx.id]))
        self.assertEqual(resp.status_code, 200)


class NavigationLinkTests(TestCase):
    def test_home_links_to_catalog(self):
        resp = self.client.get(reverse("main:show_main"))
        self.assertContains(resp, reverse("discovery:catalog"))

    def test_logged_in_nav_exposes_seller_and_buyer_paths(self):
        user = User.objects.create_user("u", password="pw12345!")
        self.client.force_login(user)
        resp = self.client.get(reverse("main:show_main"))
        for name in ("listings:create", "listings:my_listings", "transaksi:riwayat_transaksi"):
            self.assertContains(resp, reverse(name))


class PageRenderTests(TestCase):
    """Every page in the buyer/seller flow should render for a logged-in user."""

    def setUp(self):
        self.user = User.objects.create_user("u", password="pw12345!")
        self.client.force_login(self.user)

    def test_pages_render(self):
        for name in ("riwayat_transaksi", "daftar_ulasan", "dashboard_dampak"):
            resp = self.client.get(reverse(f"transaksi:{name}"))
            self.assertEqual(resp.status_code, 200, name)

    def test_riwayat_renders_with_transactions(self):
        seller = User.objects.create_user("s", password="pw12345!")
        listing = Listing.objects.create(
            seller=seller, title="Kaos", price=1000, cod_point="x"
        )
        titik = TitikCOD.objects.create(nama_lokasi="x", latitude=0, longitude=0)
        TransaksiCOD.objects.create(
            listing=StubListing.mirror_of(listing), buyer=self.user, seller=seller,
            titik_cod=titik, jadwal_temu=timezone.now() + timedelta(days=1),
        )
        resp = self.client.get(reverse("transaksi:riwayat_transaksi"))
        self.assertContains(resp, "Cek Detail Pesanan")

    def test_pengajuan_form_renders(self):
        seller = User.objects.create_user("s2", password="pw12345!")
        listing = Listing.objects.create(
            seller=seller, title="Kemeja", price=1000, cod_point="x"
        )
        resp = self.client.get(
            reverse("transaksi:ajukan_beli", args=[StubListing.mirror_of(listing).id])
        )
        self.assertEqual(resp.status_code, 200)
