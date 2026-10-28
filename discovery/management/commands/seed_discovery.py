##FOR TESTING PURPOSES

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from discovery.models import Brand, Category, Item

CATS = ["Atasan", "Bawahan", "Outer", "Sepatu", "Aksesori"]
ITEMS = [
    ("Kemeja linen oversize", "Uniqlo", 85000, 70, "Atasan", "L", "seperti_baru", "Balairung"),
    ("Kaos boxy heavyweight", "H&M", 45000, 62, "Atasan", "M", "baik", "Balairung"),
    ("Blouse satin krem", "Zara", 120000, 58, "Atasan", "S", "seperti_baru", "Perpustakaan Pusat"),
    ("Polo rajut vintage", "Lacoste", 210000, 65, "Outer", "L", "baik", "Pusat Kegiatan Mahasiswa"),
    ("Celana chino slim", "Levi's", 95000, 60, "Bawahan", "32", "baik", "Balairung"),
    ("Sneakers court putih", "Erigo", 150000, 55, "Sepatu", "42", "cukup", "Pusat Kegiatan Mahasiswa"),
]

class Command(BaseCommand):
    help = "Seed katalog dari halaman utama."

    def handle(self, *args, **opts):
        User = get_user_model()
        seller, _ = User.objects.get_or_create(username="seller.demo",
                                               defaults={"email": "seller.demo@ui.ac.id"})
        cats = {n: Category.objects.get_or_create(name=n)[0] for n in CATS}
        for name, brand, price, disc, cat, size, cond, cod in ITEMS:
            b, _ = Brand.objects.get_or_create(name=brand)
            b.categories.add(cats[cat])
            Item.objects.get_or_create(
                name=name, defaults=dict(
                    category=cats[cat], brand=b, seller=seller, price=price,
                    retail_price=round(price / (1 - disc / 100)), size=size,
                    condition=cond, cod_location=cod))
        self.stdout.write(self.style.SUCCESS("Katalog discovery ter-seed."))