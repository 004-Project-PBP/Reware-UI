##FOR TESTING PURPOSES

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from discovery.models import Brand, Category, Item

CATS = ["Atasan", "Bawahan", "Outer", "Sepatu", "Aksesori"]
ITEMS = [
    ("Kemeja linen oversize", "Uniqlo", 85000, 70, "Atasan", "L", "seperti_baru", "Balairung", "KemejaLinenOversize.png"),
    ("Kaos boxy heavyweight", "H&M", 45000, 62, "Atasan", "M", "baik", "Balairung", "kaosboxyheavyweight.png"),
    ("Blouse satin krem", "Zara", 120000, 58, "Atasan", "S", "seperti_baru", "Perpustakaan Pusat", "blousesatinkrem.jpg"),
    ("Polo rajut vintage", "Lacoste", 210000, 65, "Outer", "L", "baik", "Pusat Kegiatan Mahasiswa", "sweaterpolorajut.png"),
    ("Celana chino slim", "Levi's", 95000, 60, "Bawahan", "32", "baik", "Balairung"),
    ("Sneakers court putih", "Erigo", 150000, 55, "Sepatu", "42", "cukup", "Pusat Kegiatan Mahasiswa"),
    ("Kaos grafis band", "Uniqlo", 55000, 60, "Atasan", "L", "baik", "Stasiun UI", "kaosboxyheavyweight.png"),
    ("Kemeja flanel kotak", "H&M", 70000, 55, "Atasan", "M", "baik", "Halte Bikun FT", "KemejaLinenOversize.png"),
    ("Sweater rajut oatmeal", "Zara", 135000, 62, "Outer", "M", "seperti_baru", "Perpustakaan Pusat", "sweaterpolorajut.png"),
    ("Cardigan rajut sage", "Uniqlo", 110000, 58, "Outer", "S", "baik", "Balairung", "sweaterpolorajut.png"),
    ("Blouse putih puff", "H&M", 65000, 50, "Atasan", "S", "seperti_baru", "Kutek", "blousesatinkrem.jpg"),
    ("Celana kulot linen", "Zara", 90000, 55, "Bawahan", "M", "baik", "Stasiun UI"),
    ("Jeans straight biru", "Levi's", 160000, 60, "Bawahan", "30", "cukup", "Pusat Kegiatan Mahasiswa"),
    ("Rok plisket hitam", "H&M", 60000, 52, "Bawahan", "S", "baik", "Kutek"),
    ("Jaket denim washed", "Levi's", 185000, 65, "Outer", "L", "baik", "Halte Bikun FT"),
    ("Sepatu loafers kulit", "Lacoste", 220000, 58, "Sepatu", "41", "baik", "Balairung"),
    ("Totebag kanvas", "Erigo", 35000, 45, "Aksesori", "-", "seperti_baru", "Stasiun UI"),
    ("Topi baseball navy", "Lacoste", 50000, 50, "Aksesori", "-", "baik", "Kutek"),
]

class Command(BaseCommand):
    help = "Seed katalog dari halaman utama."

    def handle(self, *args, **opts):
        User = get_user_model()
        seller, _ = User.objects.get_or_create(username="seller.demo",
                                               defaults={"email": "seller.demo@ui.ac.id"})
        cats = {n: Category.objects.get_or_create(name=n)[0] for n in CATS}
        for name, brand, price, disc, cat, size, cond, cod, *image in ITEMS:
            b, _ = Brand.objects.get_or_create(name=brand)
            b.categories.add(cats[cat])
            item, _ = Item.objects.get_or_create(
                name=name, defaults=dict(
                    category=cats[cat], brand=b, seller=seller, price=price,
                    retail_price=round(price / (1 - disc / 100)), size=size,
                    condition=cond, cod_location=cod))
            if image and not item.image:
                src = Path(settings.BASE_DIR) / "static" / "img" / image[0]
                item.image.save(image[0], ContentFile(src.read_bytes()), save=True)
        self.stdout.write(self.style.SUCCESS("Katalog discovery ter-seed."))