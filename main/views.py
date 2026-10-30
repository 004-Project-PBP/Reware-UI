from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Avg

from .models import Brand, Category
from .forms import BrandProposalForm, BrandEditForm

from main.catalog import BRANDS, ITEMS


STATS = [
    {"value": "1.240", "label": "Pakaian berpindah tangan"},
    {"value": "± 3,2ton", "label": "ton CO₂e dihindari"},
    {"value": "Rp0", "label": "Ongkir"},
]

# file under static/img/peopleicon/, shown in the hero badge
AVATARS = [
    {"name": "Zhillan", "file": "zhillan-avatar.jpg"},
    {"name": "Razzy", "file": "razzyicon.jpeg"},
]

CATEGORIES = [
    {"name": "Atasan", "count": 128, "active": True},
    {"name": "Bawahan", "count": 94},
    {"name": "Outer", "count": 41},
    {"name": "Sepatu", "count": 57},
    {"name": "Aksesori", "count": 33},
]

STEPS = [
    {"title": "Verifikasi akun",
     "body": "Masukkan email\n@ui.ac.id, isi kode, tunggu\npersetujuan admin."},
    {"title": "Jelajah katalog",
     "body": "Telusuri Kategori → Brand\n→ Item. Penjual baru\ntampil setara."},
    {"title": "COD di titik temu",
     "body": "Sepakati waktu dan lokasi\nresmi, cek item, bayar\ndi tempat."},
    {"title": "Saling beri rating",
     "body": "Ulasan dua arah\nmembangun rekam jejak\nyang bisa dilihat semua."},
]

FAQS = [
    {"question": "Siapa yang bisa memakai Reware.ui?",
     "answer": "Hanya mahasiswa Universitas Indonesia. Kamu perlu email @ui.ac.id untuk menerima kode "
               "verifikasi, lalu admin meninjau akunmu sebelum bisa bertransaksi."},
    {"question": "Bagaimana cara pembayarannya?",
     "answer": "Pembayaran dilakukan langsung saat COD di titik temu. Reware.ui tidak memakai payment "
               "gateway, jadi cek item dulu sebelum membayar."},
    {"question": "Di mana lokasi titik temu?",
     "answer": "Titik temu adalah lokasi resmi di dalam kampus UI. Pembeli dan penjual menyepakati "
               "waktu serta lokasinya sebelum bertemu."},
    {"question": "Bagaimana sistem rating bekerja?",
     "answer": "Setelah transaksi selesai, pembeli dan penjual saling memberi ulasan. Rating dua arah "
               "ini membangun rekam jejak yang bisa dilihat semua pengguna."},
    {"question": "Apa arti persentase hemat di setiap item?",
     "answer": "Persentase hemat membandingkan harga preloved dengan harga retail item tersebut."},
]


def show_main(request):
    context = {
        "stats": STATS,
        "avatars": AVATARS,
        "categories": CATEGORIES,
        "items": ITEMS,
        "brands": BRANDS,
        "steps": STEPS,
        "faqs": FAQS,
    }
    return render(request, "index.html", context)

# module 2 - nuel
# brand_directory and filter
def brand_directory(request):
    brands = Brand.objects.all().order_by('-is_verified', 'name')
    categories = Category.objects.all()

    # Grab query parameters here
    search_query = request.GET.get('q', '').strip()
    category_name = request.GET.get('category', '').strip()
    brand_type = request.GET.get('brand_type', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    if search_query:
        brands = brands.filter(name__icontains=search_query)
    if category_name:
        brands = brands.filter(categories__name=category_name)
    if brand_type:
        brands = brands.filter(brand_type=brand_type)
    if max_price.isdigit():
        brands = brands.filter(retail_price_max__lte=int(max_price))

    brands = brands.distinct()

    context = {
        'brands': brands,
        'categories': categories,
    }
    return render(request, 'brand_directory.html', context)


# brand_detail view and restricted statistics
def brand_detail(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    # added in case Module 3 (Listing model) hasn't been merged yet
    listings = []
    active_listings_count = 0
    avg_thrift_price = 0
    avg_savings_pct = 0

    # after Module 3 links the listing model with ForeignKey(Brand, related_name='listings')
    if hasattr(brand, 'listings'):
        listings = brand.listings.filter(status='Tersedia')
        active_listings_count = listings.count()

        if request.user.is_authenticated and active_listings_count > 0:
            avg_price_val = listings.aggregate(Avg('price'))['price__avg'] or 0
            avg_thrift_price = int(avg_price_val)

            # Calculate average savings vs the brand's midpoint retail price
            mid_retail = (brand.retail_price_min + brand.retail_price_max) / 2
            if mid_retail > 0 and avg_thrift_price < mid_retail:
                avg_savings_pct = int(((mid_retail - avg_thrift_price) / mid_retail) * 100)

    context = {
        'brand': brand,
        'listings': listings,
        'active_listings_count': active_listings_count,
        'avg_thrift_price': avg_thrift_price,
        'avg_savings_pct': avg_savings_pct,
    }
    return render(request, 'brand_detail.html', context)


# propose_brand (only for logged-in users)
@login_required
def propose_brand(request):
    if request.method == 'POST':
        form = BrandProposalForm(request.POST)
        if form.is_valid():
            brand = form.save(commit=False)
            brand.is_verified = False  # Marked as "Usulan Pengguna" until admin verifies
            brand.submitted_by = request.user
            brand.save()
            form.save_m2m()  # to save the many to many categories field
            return redirect('main:brand_detail', brand_id=brand.id)
    else:
        form = BrandProposalForm()

    return render(request, 'propose_brand.html', {'form': form})


# edit_proposed_brand (only owner, before admin verifies)
@login_required
def edit_proposed_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    # reject edit if user doesn't own the proposal or if admin already verified it
    if brand.submitted_by != request.user or brand.is_verified:
        return HttpResponseForbidden("Anda tidak dapat mengedit usulan brand ini.")

    if request.method == 'POST':
        form = BrandEditForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            return redirect('main:brand_detail', brand_id=brand.id)
    else:
        form = BrandEditForm(instance=brand)

    return render(request, 'edit_brand.html', {'form': form, 'brand': brand})


# delete_proposed_brand (only owner, before admin verifies)
@login_required
@require_POST
def delete_proposed_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    if brand.submitted_by != request.user or brand.is_verified:
        return HttpResponseForbidden("Anda tidak dapat menghapus usulan brand ini.")

    brand.delete()
    return redirect('main:brand_directory')


# Follow / Unfollow Brand toggle with counter
@login_required
@require_POST
def toggle_follow_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    if request.user in brand.followers.all():
        brand.followers.remove(request.user)
        is_following = False
    else:
        brand.followers.add(request.user)
        is_following = True

    return JsonResponse({
        'status': 'success',
        'is_following': is_following,
        'follower_count': brand.followers.count(),
    })
