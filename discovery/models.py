from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    logo = models.ImageField(upload_to="img/brands/", blank=True, null=True)
    logo_width = models.PositiveSmallIntegerField(default=0)
    logo_height = models.PositiveSmallIntegerField(default=0)
    categories = models.ManyToManyField(Category, related_name="brands", blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    CONDITION_CHOICES = (
        ("baru", "Baru"),
        ("terpakai", "Terpakai"),
    )
    STATUS_CHOICES = (("tersedia", "Tersedia"), ("terjual", "Terjual"))

    name = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="items")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items_dijual")
    price = models.PositiveIntegerField(help_text="Harga jual (Rupiah)")
    retail_price = models.PositiveIntegerField(null=True, blank=True, help_text="Harga ritel dari Public API")
    size = models.CharField(max_length=16, blank=True)
    condition = models.CharField(max_length=16, choices=CONDITION_CHOICES, default="baru")
    cod_location = models.CharField(max_length=120, blank=True, help_text="Titik temu resmi di kampus")
    image = models.ImageField(upload_to="img/items/", blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="tersedia")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["category", "status"]), models.Index(fields=["price"])]

    @property
    def discount_percent(self):  # persentase hemat vs harga ritel
        if self.retail_price:
            return max(0, round((1 - self.price / self.retail_price) * 100))
        return 0

    @property
    def price_rp(self):
        return "Rp" + format(self.price, ",").replace(",", ".")

    @property
    def retail_rp(self):
        return "Rp" + format(self.retail_price, ",").replace(",", ".")

    def __str__(self):
        return f"{self.name} ({self.brand.name})"

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.size = self.size.strip()
        self.cod_location = self.cod_location.strip()
        self.condition = self.condition.strip()
        super().save(*args, **kwargs)


class WishlistItem(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="wishlist_entries")
    note = models.TextField(blank=True, help_text="Catatan pribadi buyer")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("buyer", "item")
        ordering = ["-added_at"]

    @property
    def is_sold(self):  # penanda "Terjual" di wishlist
        return self.item.status == "terjual"


class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_searches")
    label = models.CharField(max_length=120)
    keyword = models.CharField(max_length=255, blank=True)
    filters = models.JSONField(default=dict, blank=True)  # kombinasi filter tersimpan
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "saved searches"

    def querystring(self):
        from urllib.parse import urlencode
        params = dict(self.filters)
        if self.keyword:
            params["q"] = self.keyword
        return urlencode(params, doseq=True)


class SearchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_history")
    keyword = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-searched_at"]
        verbose_name_plural = "search histories"


class CuratedCollection(models.Model):
    title = models.CharField(max_length=120, default="Pilihan Kampus")
    description = models.TextField(blank=True)
    items = models.ManyToManyField(Item, through="CuratedCollectionItem", blank=True, related_name="collections")
    active_on_homepage = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CuratedCollectionItem(models.Model):
    collection = models.ForeignKey(CuratedCollection, on_delete=models.CASCADE, related_name="entries")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)  

    class Meta:
        ordering = ["position"]


class BlockedKeyword(models.Model):
    keyword = models.CharField(max_length=120, unique=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.keyword = self.keyword.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.keyword