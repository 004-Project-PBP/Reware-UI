from django.shortcuts import render


STATS = [
    {"value": "1.240", "label": "Pakaian berpindah tangan"},
    {"value": "± 3,2ton", "label": "ton CO₂e dihindari"},
    {"value": "Rp0", "label": "Ongkir"},
]

CATEGORIES = [
    {"name": "Atasan", "count": 128, "active": True},
    {"name": "Bawahan", "count": 94},
    {"name": "Outer", "count": 41},
    {"name": "Sepatu", "count": 57},
    {"name": "Aksesori", "count": 33},
]

ITEMS = [
    {"name": "Kemeja linen oversize", "brand": "Uniqlo", "price": "Rp85.000", "discount": 70},
    {"name": "Kaos boxy heavyweight", "brand": "H&M", "price": "Rp45.000", "discount": 62},
    {"name": "Blouse satin krem", "brand": "Zara", "price": "Rp120.000", "discount": 58},
    {"name": "Polo rajut vintage", "brand": "Lacoste", "price": "Rp210.000", "discount": 65},
    {"name": "Item 5", "brand": "Price 5", "price": "Rp210.000", "discount": 67},
    {"name": "Item 6", "brand": "Item 6", "price": "Rp210.000", "discount": 76},
]

# file under static/img/brands/, display size from the design
BRANDS = [
    {"name": "Levi's", "file": "levis.png", "width": 99, "height": 48},
    {"name": "Zara", "file": "zara.png", "width": 106, "height": 45},
    {"name": "Uniqlo", "file": "uniqlo.png", "width": 107, "height": 60},
    {"name": "Erigo", "file": "erigo.png", "width": 155, "height": 26},
    {"name": "H&M", "file": "hm.png", "width": 62, "height": 62},
    {"name": "Lacoste", "file": "lacoste.png", "width": 92, "height": 92},
    {"name": "Colorbox", "file": "colorbox.png", "width": 104, "height": 104},
    {"name": "et cetera", "file": "etcetera.png", "width": 92, "height": 81},
    {"name": "Urban&Co", "file": "urbanco.png", "width": 122, "height": 122},
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
        "categories": CATEGORIES,
        "items": ITEMS,
        "brands": BRANDS,
        "steps": STEPS,
        "faqs": FAQS,
    }
    return render(request, "index.html", context)
