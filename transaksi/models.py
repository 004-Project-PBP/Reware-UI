import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from listings.models import Listing
from main.models import Category as StubCategory  # Import the StubCategory model from the same app

class StubListing(models.Model):
    class ListingStatus(models.TextChoices):
        TERSEDIA = 'TERSEDIA', 'Tersedia'
        DIPESAN = 'DIPESAN', 'Dipesan'
        TERJUAL = 'TERJUAL', 'Terjual'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='stub_listings'
    )
    category = models.ForeignKey(StubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.OneToOneField(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaksi_mirror',
        help_text="Listing Modul 3 yang dicerminkan oleh stub ini",
    )
    title = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, 
        choices=ListingStatus.choices, 
        default=ListingStatus.TERSEDIA
    )

    def __str__(self):
        return self.title

    @classmethod
    def mirror_of(cls, listing):
        """Get or create the stub that mirrors a Modul 3 Listing."""
        stub, _ = cls.objects.get_or_create(
            source=listing,
            defaults={'seller': listing.seller, 'title': listing.title},
        )
        stub.seller = listing.seller
        stub.title = listing.title
        stub.selling_price = listing.price
        stub.retail_price = listing.retail_price or 0
        # hanya listing yang masih tersedia yang boleh diajukan
        if listing.status == 'available':
            stub.status = cls.ListingStatus.TERSEDIA
        elif listing.status == 'booked':
            stub.status = cls.ListingStatus.DIPESAN
        elif listing.status == 'sold':
            stub.status = cls.ListingStatus.TERJUAL
        stub.save()
        return stub

    def sync_status_to_source(self):
        """Push this stub's status back to the Modul 3 Listing."""
        if not self.source_id:
            return
        mapping = {
            self.ListingStatus.TERSEDIA: 'available',
            self.ListingStatus.DIPESAN: 'booked',
            self.ListingStatus.TERJUAL: 'sold',
        }
        self.source.status = mapping[self.status]
        self.source.save(update_fields=['status'])


class TitikCOD(models.Model):
    
    """Master Titik COD Kampus (Stasiun UI, Perpustakaan Pusat, Balairung, Halte Bikun, dll.)
    Integrated with WebGIS / Google Maps API."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_lokasi = models.CharField(max_length=150) 
    deskripsi_detail = models.TextField(blank=True, help_text="Patokan spesifik lokasi temu")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True, help_text="False jika titik COD sudah tidak digunakan")

    def __str__(self):
        return self.nama_lokasi


class TransaksiCOD(models.Model):
    
    """Alur Status Transaksi: Diajukan -> Disetujui -> Selesai / Dibatalkan"""    
    class StatusTransaksi(models.TextChoices):
        DIAJUKAN = 'DIAJUKAN', 'Diajukan'
        DISETUJUI = 'DISETUJUI', 'Disetujui'
        SELESAI = 'SELESAI', 'Selesai'
        DIBATALKAN = 'DIBATALKAN', 'Dibatalkan'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    listing = models.ForeignKey(
        StubListing,
        on_delete=models.CASCADE, 
        related_name='transaksi_cod'
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='pembelian_cod'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='penjualan_cod'
    )
    titik_cod = models.ForeignKey(
        TitikCOD, 
        on_delete=models.PROTECT, 
        related_name='transaksi'
    )
    
    jadwal_temu = models.DateTimeField(help_text="Tanggal dan jam janjian COD")
    catatan_buyer = models.TextField(blank=True, help_text="Catatan tambahan atau kontak darurat")
    
    status = models.CharField(
        max_length=20,
        choices=StatusTransaksi.choices,
        default=StatusTransaksi.DIAJUKAN
    )
    
    alasan_batal = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Diisi jika ditolak seller atau dibatalkan buyer" 
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        # Prevent a user from buying their own item
        if self.buyer == self.seller:
            raise ValidationError("Buyer tidak dapat mengajukan pembelian pada barang miliknya sendiri.")

    def save(self, *args, **kwargs):
        # Auto-populate seller from the listing so it never mismatches
        if not self.seller_id and self.listing:
            self.seller = self.listing.seller
        super().save(*args, **kwargs)

    @property
    def penghematan_rupiah(self):
        #Calculates savings: Retail Price - Selling Price
        diff = self.listing.retail_price - self.listing.selling_price
        return max(diff, 0)

    def __str__(self):
        return f"COD: {self.listing.title} | Buyer: {self.buyer.username} ({self.get_status_display()})"


class Ulasan(models.Model):
    
    """Two-way review system: Buyer rates Seller, Seller rates Buyer after status is 'SELESAI'."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaksi = models.ForeignKey(
        TransaksiCOD, 
        on_delete=models.CASCADE, 
        related_name='ulasan_list'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ulasan_diberikan'
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ulasan_diterima'
    )
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    komentar = models.TextField(max_length=500, help_text="Ulasan singkat transaksi")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures a user can only write one review per transaction (allows two-way: 1 from buyer, 1 from seller)
        constraints = [
            models.UniqueConstraint(
                fields=['transaksi', 'reviewer'], 
                name='unique_review_per_party_per_transaction'
            )
        ]
        ordering = ['-created_at']

    def clean(self):
        if self.transaksi.status != TransaksiCOD.StatusTransaksi.SELESAI:
            raise ValidationError("Ulasan hanya dapat ditulis setelah transaksi berstatus Selesai.")
        if self.reviewer not in [self.transaksi.buyer, self.transaksi.seller]:
            raise ValidationError("Hanya pihak yang terlibat dalam transaksi yang dapat memberi ulasan.")
        if self.reviewer == self.reviewee:
            raise ValidationError("Tidak dapat memberi ulasan kepada diri sendiri.")

    def __str__(self):
        return f"Ulasan {self.reviewer.username} -> {self.reviewee.username} ({self.rating}/5)"