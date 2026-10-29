from django.shortcuts import render

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
