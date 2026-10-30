from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.catalog import BRANDS


FACULTY_CHOICES = [
    ("FK", "Kedokteran"),
    ("FKG", "Kedokteran Gigi"),
    ("FF", "Farmasi"),
    ("FKM", "Kesehatan Masyarakat"),
    ("FIK", "Ilmu Keperawatan"),
    ("FMIPA", "Matematika dan Ilmu Pengetahuan Alam"),
    ("FT", "Teknik"),
    ("FASILKOM", "Ilmu Komputer"),
    ("FH", "Hukum"),
    ("FEB", "Ekonomi dan Bisnis"),
    ("FIB", "Ilmu Pengetahuan Budaya"),
    ("FPSI", "Psikologi"),
    ("FISIP", "Ilmu Sosial dan Ilmu Politik"),
    ("FIA", "Ilmu Administrasi"),
    ("VOKASI", "Program Pendidikan Vokasi"),
]

# Official campus meeting points for COD
COD_POINT_CHOICES = [
    ("stasiun-ui", "Stasiun UI"),
    ("perpustakaan-pusat", "Perpustakaan Pusat"),
    ("balairung", "Balairung"),
    ("pusgiwa", "Pusgiwa"),
    ("masjid-ui", "Masjid Ukhuwah Islamiyah"),
    ("kutek", "Area Kutek"),
]

BRAND_CHOICES = [(brand["name"], brand["name"]) for brand in BRANDS]


class Profile(models.Model):
    ROLE_CHOICES = [
        ("buyer", "Buyer"),
        ("seller", "Seller"),
    ]
    # Fields a user fills in on "Lengkapi profil"
    COMPLETION_FIELDS = ["display_name", "faculty", "batch", "phone", "cod_point"]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")
    display_name = models.CharField("nama tampilan", max_length=60, blank=True)
    faculty = models.CharField("fakultas", max_length=10, choices=FACULTY_CHOICES, blank=True)
    batch = models.PositiveSmallIntegerField(
        "angkatan", null=True, blank=True,
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )
    phone = models.CharField(
        "nomor kontak", max_length=16, blank=True,
        validators=[RegexValidator(r"^\+?\d{9,15}$", "Nomor kontak berisi 9-15 angka, boleh diawali +.")],
    )
    photo_url = models.URLField("URL foto profil", blank=True)
    cod_point = models.CharField("titik COD favorit", max_length=30, choices=COD_POINT_CHOICES, blank=True)
    is_verified = models.BooleanField("terverifikasi", default=False)

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.display_name or self.user.first_name or self.user.username

    @property
    def is_complete(self):
        return all(getattr(self, field) for field in self.COMPLETION_FIELDS)

    @property
    def badges(self):
        """(label, pill tone) pairs shown next to the name."""
        badges = [(self.get_role_display(), "olive")]
        if self.is_verified:
            badges.append(("Terverifikasi", "green"))
        if self.is_complete:
            badges.append(("Profil lengkap", "green"))
        if self.user.is_staff:
            badges.append(("Admin", "muted"))
        return badges


class FavoriteBrand(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_brands")
    brand = models.CharField(max_length=40, choices=BRAND_CHOICES)

    class Meta:
        ordering = ["brand"]
        constraints = [
            models.UniqueConstraint(fields=["user", "brand"], name="unique_favorite_brand"),
        ]

    def __str__(self):
        return f"{self.user} - {self.brand}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    # Every account gets a profile, whether it came from register, SSO, admin, or createsuperuser
    if created:
        Profile.objects.create(user=instance)
