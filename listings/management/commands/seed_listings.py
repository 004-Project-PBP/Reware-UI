import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from listings.models import Listing

User = get_user_model()

SEED_SELLERS = ["seed_ayu", "seed_bima", "seed_citra"]

# (judul, harga ritel)
BASE_ITEMS = [
    ("Uniqlo Oversized Tee", 199000),
    ("Uniqlo Flannel Shirt", 299000),
    ("Zara Wide Leg Pants", 499000),
    ("Zara Linen Shirt", 399000),
    ("Nike Windbreaker", 899000),
    ("Nike Dri-FIT Tee", 449000),
    ("Erigo Denim Jacket", 349000),
    ("Erigo Hoodie", 299000),
    ("H&M Knit Cardigan", 349000),
    ("H&M Straight Jeans", 399000),
    ("Converse Chuck 70", 1299000),
    ("Adidas Track Jacket", 799000),
    ("Cotton Ink Kemeja Batik", 249000),
    ("Lacoste Polo Shirt", 1199000),
    ("Levi's 501 Jeans", 1499000),
    ("Pull&Bear Cargo Pants", 459000),
    ("Bershka Crop Top", 249000),
    ("Uniqlo Ultra Light Down", 799000),
    ("Vans Old Skool", 999000),
    ("Thrift Corduroy Jacket", 450000),
]

COD_POINTS = [
    "Stasiun UI", "Perpustakaan UI", "Gedung Fasilkom",
    "Halte Kutek", "Balairung UI",
]
DESCRIPTIONS = [
    "Dipakai beberapa kali, kondisi masih rapi.",
    "Tidak ada cacat kain, tinggal pakai.",
    "Noda tipis hampir tidak terlihat.",
    "Jarang dipakai, ukuran kurang pas.",
    "Preloved terawat, sudah dicuci bersih.",
]
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
STATUS_POOL = ["available"] * 7 + ["booked"] * 1 + ["sold"] * 1 + ["archived"] * 1


class Command(BaseCommand):
    help = "Isi database dengan data contoh listing (seed/demo)."

    def handle(self, *args, **options):
        rng = random.Random(42)  # hasil sama setiap kali dijalankan
        conditions = [c[0] for c in Listing._meta.get_field("condition").choices]

        sellers = []
        for username in SEED_SELLERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("seedpass123")
                user.save()
            sellers.append(user)

        created_count = 0
        for seller in sellers:
            for title, retail in BASE_ITEMS:
                price = max(10000, round(retail * rng.uniform(0.3, 0.7) / 5000) * 5000)
                _, created = Listing.objects.get_or_create(
                    seller=seller,
                    title=title,
                    defaults=dict(
                        description=rng.choice(DESCRIPTIONS),
                        size=rng.choice(SIZES),
                        condition=rng.choice(conditions),
                        price=price,
                        retail_price=retail,
                        stock=rng.choice([1, 1, 1, 2, 3]),
                        cod_point=rng.choice(COD_POINTS),
                        status=rng.choice(STATUS_POOL),
                    ),
                )
                created_count += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"{created_count} listing baru dibuat. Total sekarang: {Listing.objects.count()}."
        ))