from django.urls import path
from . import views

app_name = 'transaksi'

urlpatterns = [
    # History and Details
    path('riwayat/', views.transaction_history, name='riwayat_transaksi'),
    path('<uuid:transaksi_id>/', views.detail_transaksi, name='detail_transaksi'),

    # Buyer CRUD
    path('ajukan/<int:listing_id>/', views.ajukan_beli, name='ajukan_beli'),
    path('<uuid:transaksi_id>/edit/', views.edit_pengajuan, name='edit_pengajuan'),
    path('<uuid:transaksi_id>/batal/', views.batalkan_pengajuan, name='batalkan_pengajuan'),

    # Seller Actions (AJAX + POST)
    path('<uuid:transaksi_id>/respon/', views.respon_pengajuan_ajax, name='respon_pengajuan_ajax'),
    path('<uuid:transaksi_id>/selesai/', views.selesaikan_transaksi, name='selesaikan_transaksi'),

    # Reviews (Ulasan)
    path('ulasan/', views.daftar_ulasan, name='daftar_ulasan'),
    path('<uuid:transaksi_id>/ulasan/submit/', views.submit_ulasan_ajax, name='submit_ulasan_ajax'),
    path('ulasan/<uuid:ulasan_id>/hapus/', views.hapus_ulasan, name='hapus_ulasan'),

    # Impact Dashboard & AJAX Endpoints
    path('dampak/', views.dashboard_dampak, name='dashboard_dampak'),
    path('api/dampak/', views.api_dampak_data, name='api_dampak_data'),
    path('api/navbar-counter/', views.api_navbar_counter, name='api_navbar_counter'),
]