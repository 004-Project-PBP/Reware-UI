from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.test import TestCase

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