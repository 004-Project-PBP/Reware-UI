import random
import requests
from django.core.management.base import BaseCommand
from main.models import Brand, Category

class Command(BaseCommand):
    help = 'Clears old data and seeds 50+ fashion brands from DummyJSON'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning old seeded brands and fetching new data...")

        # Wipe old items except user submitted ones
        Brand.objects.filter(submitted_by__isnull=True).delete()

        # Map categories from dummyjson
        category_map = {
            'mens-shirts': 'Atasan',
            'tops': 'Atasan',
            'womens-dresses': 'Bawahan',
            'mens-shoes': 'Sepatu',
            'womens-shoes': 'Sepatu',
            'mens-watches': 'Aksesori',
            'womens-watches': 'Aksesori',
            'womens-bags': 'Aksesori',
            'womens-jewellery': 'Aksesori',
            'sunglasses': 'Aksesori',
        }

        master_categories = ['Atasan', 'Bawahan', 'Outerwear', 'Sepatu', 'Aksesori']
        cat_objects = {}
        for cat_name in master_categories:
            cat_obj, _ = Category.objects.get_or_create(name=cat_name)
            cat_objects[cat_name] = cat_obj

        brand_types = ['Fast Fashion', 'Lokal', 'Premium', 'Vintage']
        USD_TO_IDR = 16000
        created_count = 0

        # Fetch from the 10 fashion endpoints in the API
        fashion_items = []
        for api_cat, local_cat_name in category_map.items():
            url = f'https://dummyjson.com/products/category/{api_cat}'
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('products', []):
                        item['_local_category'] = local_cat_name
                        fashion_items.append(item)
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error fetching {api_cat}: {e}"))

        # Create a unique brand entry for each item
        for item in fashion_items:
            raw_brand = item.get('brand')
            title = item.get('title', 'Fashion')
            
            base_name = raw_brand if raw_brand else f"{title.split()[0]} Studio"
            brand_name = base_name
            if Brand.objects.filter(name=brand_name).exists():
                brand_name = f"{base_name} · {title}"

            price_idr = int(float(item.get('price', 25)) * USD_TO_IDR)
            min_price = int(price_idr * 0.8)
            max_price = int(price_idr * 1.2)

            brand_obj, created = Brand.objects.update_or_create(
                name=brand_name,
                defaults={
                    'logo_url': item.get('thumbnail', ''),
                    'brand_type': random.choice(brand_types),
                    'retail_price_min': min_price,
                    'retail_price_max': max_price,
                    'is_verified': True,
                }
            )
            brand_obj.categories.add(cat_objects[item['_local_category']])
            if created:
                created_count += 1

        # Add 5 extra real fashion brands
        extra_fashion_brands = [
            ('Erigo Apparel', 'Lokal', 'Outerwear', 150000, 450000),
            ('Uniqlo Indonesia', 'Fast Fashion', 'Outerwear', 299000, 899000),
            ('The Executive', 'Lokal', 'Atasan', 199000, 599000),
            ('Compass Shoes', 'Lokal', 'Sepatu', 400000, 850000),
            ('Pull&Bear Vintage', 'Vintage', 'Outerwear', 250000, 650000),
        ]
        sample_thumb = fashion_items[0].get('thumbnail', '') if fashion_items else ''

        for b_name, b_type, b_cat, p_min, p_max in extra_fashion_brands:
            brand_obj, created = Brand.objects.update_or_create(
                name=b_name,
                defaults={
                    'logo_url': sample_thumb,
                    'brand_type': b_type,
                    'retail_price_min': p_min,
                    'retail_price_max': p_max,
                    'is_verified': True,
                }
            )
            brand_obj.categories.add(cat_objects[b_cat])
            if created:
                created_count += 1

        total = Brand.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Done! {total} brands seeded successfully."))