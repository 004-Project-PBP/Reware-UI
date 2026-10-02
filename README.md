# Reware.ui
Reware.ui adalah marketplace pakaian preloved yang aksesnya terbatas pada mahasiswa Universitas Indonesia terverifikasi. Aplikasi ini memindahkan transaksi thrift antarmahasiswa dari grup percakapan ke dalam satu katalog terstruktur.

# Reware.ui Marketplace Preloved Mahasiswa UI

## Deployment
- **Link PWS:** https://zhillan-baniaksa-rewareui.pws.cs.ui.ac.id/

## Deskripsi Aplikasi

Reware.ui adalah marketplace pakaian preloved yang aksesnya terbatas pada mahasiswa Universitas Indonesia terverifikasi. Aplikasi ini memindahkan transaksi thrift antarmahasiswa dari grup percakapan ke dalam satu katalog terstruktur, dengan lima komponen utama:

- **Katalog berjenjang** penelusuran mengikuti hirarki Kategori → Brand → Item, sehingga penjual baru tetap memperoleh keterpaparan yang setara.
- **Verifikasi identitas kampus** registrasi mensyaratkan verifikasi kode dari email `@ui.ac.id`, lalu diverifikasi admin sebelum akun dapat bertransaksi.
- **Serah terima di titik kampus** transaksi dilakukan secara COD pada titik temu resmi di area kampus, tanpa gerbang pembayaran dan tanpa pengiriman.
- **Penilaian dua arah** pembeli dan penjual saling memberi rating setelah transaksi selesai, membentuk rekam jejak yang terlihat publik.
- **Indikator dampak** setiap item menampilkan persentase penghematan terhadap harga ritel, dan setiap pengguna memiliki rekap dampak lingkungan pribadi.

Aplikasi ini merupakan bagian dari tema **Sustainable Living**, sub-tema **Slow Fashion & Conscious Shopping**.

## Anggota Kelompok & Pembagian Modul

| No | Modul | Nama | NPM |
|---|---|---|---|
| 1 | Landing Page, Autentikasi, Profil Mahasiswa | Zhillan Baniaksa | 2506637174 |
| 2 | Katalog Brand & Referensi Harga (Public API) | Abraham Imanuel | 2506554890 |
| 3 | Lapak Thrift: Listing & Inventory Management | Maglio Razzy | 2506553616 |
| 4 | Discovery, Filter & Wishlist | Kevin Nicholas Santoso | 2506637041 |
| 5 | Transaksi COD, Ulasan & Dampak Lingkungan | Nanda Athaillah Nurano | 2506557425 |

## Daftar Modul

1. **Landing Page, Autentikasi, Profil Mahasiswa** Infrastruktur identitas pengguna: registrasi berbasis peran (Seller/Buyer, satu akun bisa keduanya), verifikasi status mahasiswa UI lewat kode verifikasi yang dikirim ke email `@ui.ac.id` (via Brevo/Mailjet API), lalu diverifikasi admin sebelum akun dapat bertransaksi, login/logout via Django Auth, manajemen profil (fakultas, angkatan, titik COD favorit, badge verifikasi & rating), serta panel admin untuk memverifikasi/memblokir akun.

2. **Katalog Brand & Referensi Harga (Public API)** Master data brand fashion beserta harga ritel acuan yang diambil dari **Public API**, menjadi sumber data bersama bagi modul lain (dipakai untuk menghitung persentase penghematan pada tiap listing). Termasuk direktori brand, follow/unfollow brand, dan usulan brand baru dari pengguna.

3. **Lapak Thrift: Listing & Inventory Management** Form bagi seller untuk mengunggah item preloved (judul, foto, brand, kategori, ukuran, kondisi, harga, stok, titik COD), kalkulator penghematan otomatis terhadap harga ritel (Modul 2), manajemen status listing (Tersedia/Dibooking/Terjual/Diarsipkan), dan dashboard "My Listings" bagi seller.

4. **Discovery, Filter & Wishlist** Navigasi pencarian hierarkis (Kategori → Brand → Item), mesin pencarian dengan filter gabungan (kategori, brand, ukuran, kondisi, rentang harga), sorting (Terbaru/Termurah/Paling Hemat), wishlist dengan catatan pribadi, serta pencarian tersimpan.

5. **Transaksi COD, Ulasan & Dampak Lingkungan** Alur pengajuan beli hingga serah terima COD di titik-titik kampus UI (Diajukan → Disetujui → Selesai/Dibatalkan). Titik temu COD ditentukan lewat integrasi **Google Maps API**, di mana buyer dan seller sama-sama bisa memilih/menyepakati lokasi ketemuan di peta transaksi tetap sepenuhnya COD, Maps hanya dipakai untuk menentukan dan menampilkan lokasi, bukan pembayaran atau pengiriman. Modul ini juga mencakup ulasan & rating dua arah antara buyer-seller setelah transaksi selesai, serta dashboard dampak lingkungan (jumlah item terselamatkan, total penghematan, estimasi air & CO2 yang dihemat).

*(Alur pengguna Buyer: Landing Page → Jelajah Kategori → Detail Item → Login & Verifikasi → Ajukan Beli → Seller Setujui → COD di Kampus → Ulasan Dua Arah → Rating Naik → Dashboard Dampak. Alur pengguna Seller: Login Seller → Lengkapi Profil → Form Jual Barang → Listing Tayang → Masuk Katalog → Pengajuan Masuk → Setujui/Tolak → COD di Kampus → Selesai & Ulasan.)*

## Public API / Mock API

- **DummyJSON Products API** digunakan pada Modul 2 untuk seeding data brand, kategori, foto, dan harga ritel acuan (endpoint kategori seperti `mens-shirts`, `womens-dresses`, `tops`, dll.) melalui Django management command, menghasilkan 50+ data referensi saat deploy.
- **Brevo/Mailjet API** digunakan pada Modul 1 untuk mengirim kode verifikasi ke email `@ui.ac.id` saat registrasi akun.
- **Google Maps API / Other Webgis API** digunakan pada Modul 5 untuk menentukan dan menampilkan titik temu COD antara buyer dan seller.
- **Alternatif:** Open Supply Hub API, untuk melengkapi data negara produksi brand.

## Jenis/Role Pengguna

- **Buyer** menelusuri katalog, memfilter & mencari item, menyimpan wishlist, mengajukan pembelian, memberi ulasan setelah transaksi selesai.
- **Seller** membuat & mengelola listing, menyetujui/menolak pengajuan beli, menerima ulasan dari buyer. *(Satu akun dapat berperan sebagai Buyer dan Seller sekaligus.)*
- **Admin** memverifikasi akun & brand baru, mengelola master data (kategori, tingkat kondisi, titik COD kampus), menengahi sengketa transaksi, serta memoderasi listing/ulasan yang melanggar aturan.
- **Tamu (belum login)** hanya dapat melihat katalog publik secara terbatas (foto, harga, brand, ukuran); fitur seperti wishlist, kontak seller, dan riwayat transaksi hanya tampil bagi pengguna yang sudah login (*authentication-based filtering*).

## Desain (Figma)

- **Link Figma:** https://www.figma.com/team_invite/redeem/25EXG65UrUL0XNTQguXPb5?t=AncRCZS0A4oMweSB-21

## Repository

- **Link Git:** (https://github.com/004-Project-PBP/Reware.ui)

## Modules Division

- **Link Sheet** (https://docs.google.com/spreadsheets/d/1eij5laoQNBbDALTZZCPAx-dQcgcHD6lEt02KRg633ac/edit?usp=sharing)
