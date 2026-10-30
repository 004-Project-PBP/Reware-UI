from django.conf import settings
from django.db import models


class Listing(models.Model):
    class Condition(models.TextChoices):
        LIKE_NEW = "like_new", "Like New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Tersedia"
        BOOKED = "booked", "Dibooking"
        SOLD = "sold", "Terjual"
        ARCHIVED = "archived", "Diarsipkan"

    SIZE_CHOICES = [
        ("XS", "XS"), ("S", "S"), ("M", "M"),
        ("L", "L"), ("XL", "XL"), ("XXL", "XXL"),
        ("ALL", "All Size"),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    brand = models.ForeignKey(
        "main.Brand", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="listings",
    )
    category = models.ForeignKey(
        "main.Category", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="listings",
    )
    photo = models.ImageField(upload_to="listings/", blank=True, null=True)
    size = models.CharField(max_length=3, choices=SIZE_CHOICES, default="M")
    condition = models.CharField(
        max_length=10, choices=Condition.choices, default=Condition.GOOD
    )
    price = models.PositiveIntegerField()
    retail_price = models.PositiveIntegerField(null=True, blank=True)  
    stock = models.PositiveIntegerField(default=1)
    cod_point = models.CharField(max_length=100)  # sementara, nanti ganti sesuai Modul 5
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    
    @property
    def savings_percent(self):
        if self.retail_price and self.retail_price > self.price:
            return round((self.retail_price - self.price) / self.retail_price * 100)
        return None
    
    def save(self, *args, **kwargs):
        if self.brand_id and not self.retail_price:
            low, high = self.brand.retail_price_min, self.brand.retail_price_max
            if high:
                self.retail_price = (low + high) // 2
        super().save(*args, **kwargs)
        