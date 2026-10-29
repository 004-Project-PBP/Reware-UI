from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import StubListing, TitikCOD, TransaksiCOD, StubCategory, Ulasan
from .forms import PengajuanBeliForm,UlasanForm
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.paginator import Paginator

# 1. BUYER & SELLER: READ & FILTER HISTORY
@login_required
def transaction_history(request):
    """History page
    Filters by role (buyer/seller), status pills, search query, category, brand, and date range."""

    role = request.GET.get('peran','buyer') #'buyer' or 'seller'
    statusFilter= request.GET.get('status','')
    searchQuery= request.GET.get('q','')
    filterCategory= request.GET.get('kategori', '')
    filterBrand= request.GET.get('brand', '')
    startDate= request.GET.get('start_date','')
    endDate=request.GET.get ('end_date','')

    if (role =='seller'):
        querySet=TransaksiCOD.objects.filter(seller=request.user)
    else:
        querySet=TransaksiCOD.objects.filter(buyer=request.user)

    if statusFilter:
        querySet=querySet.filter(status=statusFilter) 
    if searchQuery:
        querySet= querySet.filter(
            Q(listing__title__icontains=searchQuery)|
            Q(id__icontains=searchQuery)
        )

    if filterCategory:
        querySet=querySet.filter(listing__category_id=filterCategory)
    
    if filterBrand:
        querySet=querySet.filter(listing__brand_id=filterBrand)

    
    if startDate:
        querySet=querySet.filter(jadwal_temu__date__gte=startDate)

    
    if endDate:
        querySet=querySet.filter(jadwal_temu__date__lte=endDate)

    querySet = querySet.select_related('listing', 'titik_cod', 'buyer', 'seller')

    paginator = Paginator(querySet, 5) # 5 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #Pass the current query parameters to the template for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'transaksi_list': page_obj,  
        'query_string': query_params.urlencode(), # Pass the URL filters
        'categories': StubCategory.objects.all(),
        'current_role': role,
        'current_status': statusFilter,
        'search_query': searchQuery,
    }
    return render(request, 'transaksi/riwayat_transaksi.html', context)

@login_required
def detail_transaksi(request, transactionID):
    """
    View COD shedule details & counterparty contact
    Strictly visible only to the buyer and seller involved
    """
    transaction=get_object_or_404(TransaksiCOD,id=transactionID)
    if request.user != transaction.buyer and request.user != transaction.seller:
        return HttpResponseForbidden("Akses ditolak: Anda tidak terlibat dalam transaksi ini.")

    userUlasan= Ulasan.objects.filter(transaksi=transaction, reviewer=request.user).first()

    context ={
        'transaksi':transaction,
        'is_buyer':request.user==transaction.buyer,
        'is_seller':request.user==transaction.seller,
        'user_ulasan':userUlasan,
        'ulasan_form':UlasanForm(instance=userUlasan),
    }
    return render(request,'transaksi/detail_transaksi.html',context)

#Buyer pov : Create, Update, Cancer COD

@login_required
def ajukan_beli(request,listing_id):
    """
    Buyer submits and order request on an avail listing 
    """
    listing = get_object_or_404(StubListing,id=listing_id)
    if listing.status!= StubListing.ListingStatus.TERSEDIA:
        messages.error (request, "Maaf, item ini sudah tidak tersedia")
        return redirect ('transaksi:riwayat_transaksi')

    if listing.seller == request.user:
        messages.error(request, "Anda tidak bisa mengajukan pembelian pada barang sendiri.")
        return redirect('transaksi:riwayat_transaksi')

    existing = TransaksiCOD.objects.filter(
        listing=listing,
        buyer=request.user,
        status__in=[TransaksiCOD.StatusTransaksi.DIAJUKAN, TransaksiCOD.StatusTransaksi.DISETUJUI]
    ).exists()
    if existing:
        messages.warning(request, "Anda sudah memiliki pengajuan aktif untuk item ini.")
        return redirect('transaksi:riwayat_transaksi')

    if request.method == 'POST':
        form = PengajuanBeliForm(request.POST)
        if form.is_valid():
            transaksi = form.save(commit=False)
            transaksi.listing = listing
            transaksi.buyer = request.user
            transaksi.seller = listing.seller
            transaksi.status = TransaksiCOD.StatusTransaksi.DIAJUKAN
            transaksi.save()
            messages.success(request, "Pengajuan beli berhasil dikirim!")
            return redirect('transaksi:detail_transaksi', transaksi_id=transaksi.id)
    else:
        form = PengajuanBeliForm()

    titik_cod_list = list(TitikCOD.objects.filter(is_active=True).values(
        'id', 'nama_lokasi', 'deskripsi_detail', 'latitude', 'longitude'
    ))
    context={
        'form': form,
        'listing': listing,
        'titik_cod_list': titik_cod_list,
        'is_edit': False
    }
    return render(request, 'transaksi/form_pengajuan.html', context)

@login_required
def edit_pengajuan(request, transaksi_id):
    """UPDATE Change schedule/COD location ONLY while status is DIAJUKAN."""
    transaksi = get_object_or_404(TransaksiCOD, id=transaksi_id, buyer=request.user)

    if transaksi.status != TransaksiCOD.StatusTransaksi.DIAJUKAN:
        messages.error(request, "Pengajuan tidak dapat diubah karena sudah diproses seller.")
        return redirect('transaksi:detail_transaksi', transaksi_id=transaksi.id)

    if request.method == 'POST':
        form = PengajuanBeliForm(request.POST, instance=transaksi)
        if form.is_valid():
            form.save()
            messages.success(request, "Jadwal dan titik COD berhasil diperbarui.")
            return redirect('transaksi:detail_transaksi', transaksi_id=transaksi.id)
    else:
        form = PengajuanBeliForm(instance=transaksi)

    titik_cod_list = list(TitikCOD.objects.filter(is_active=True).values(
        'id', 'nama_lokasi', 'deskripsi_detail', 'latitude', 'longitude'
    ))
    context={
        'form': form,
        'listing': transaksi.listing,
        'transaksi': transaksi,
        'titik_cod_list': titik_cod_list,
        'is_edit': True
     }
    return render(request, 'transaksi/form_pengajuan.html', context)

@login_required
@require_POST
def batalkan_pengajuan(request, transaksi_id):
    """Delete/Cancel the ongoing transaction (Only when status is DIAJUKAN)"""
    transaksi = get_object_or_404(TransaksiCOD, id=transaksi_id, buyer=request.user)
    if transaksi.status==TransaksiCOD.StatusTransaksi.DIAJUKAN:
        transaksi.status=TransaksiCOD.StatusTransaksi.DIBATALKAN
        transaksi.alasan_batal= "Dibatalkan oleh pembeli."
        transaksi.save()
        messages.info(request,"Pengajuan pembelian telah dibatalkan.")
        return redirect('transaksi:riwayat_transaksi')
    messages.error(request,"Pengajuan yang sudah di proses tidak dapat dibatalkan.")
    return redirect('transaksi:riwayat_transaksi')


# SELLER POV : Approve, Reject, Complete 

@login_required
@require_POST
def respon_pengajuan_ajax(request,transaksi_id):
    """
    Update : Approve or reject a request
    Approving automatically updates Module 3 listing status and auto-rejects competing requests
    """
    transaksi=get_object_or_404(TransaksiCOD, id=transaksi_id, seller=request.user)
    aksi=request.POST.get('aksi') #'setujui' or 'tolak'

    if aksi=='setujui':
        transaksi.status=TransaksiCOD.StatusTransaksi.DISETUJUI
        transaksi.save()

        #update listing in module 3
        listing=transaksi.listing
        listing.status=StubListing.ListingStatus.DIPESAN
        listing.save()

        TransaksiCOD.objects.filter(
            listing=listing,
            status= TransaksiCOD.StatusTransaksi.DIAJUKAN
        ).exclude(id=transaksi.id).update(
            status=TransaksiCOD.StatusTransaksi.DIBATALKAN,
            alasan_batal="Otomatis ditolak karena pembeli lain telah disetujui."

        )
        context ={
            'success':1==1,
            'new_status': transaksi.get_status_display(),
            'message': 'Pengajuan disetujui!'
        }
        return JsonResponse(context)

    elif aksi=='tolak':
        alasan=request.POST.get('alasan','Ditolak oleh penjual')
        transaksi.status= TransaksiCOD.StatusTransaksi.DIBATALKAN
        transaksi.alasan_batal= alasan

        transaksi.alasan_batal = strip_tags(alasan) #sanitization to prevent XSS attacks
        
        transaksi.save()
        context={
            'success':1==1,
            'new_status':transaksi.get_status_display(),
            'message':'Pengajuan ditolak!'
        }
        return JsonResponse(context)
    context={
        'success': 1==0,
        'message': 'Aksi tidak valid.'
    }
    return JsonResponse(context,status=400)

@login_required
@require_POST
def selesaikan_transaksi(request,transaksi_id):
    """Update (Seller pov version) mark transaction as selesai after campus COD meetup"""
    transaksi=get_object_or_404(TransaksiCOD, id=transaksi_id, seller=request.user)

    if transaksi.status==TransaksiCOD.StatusTransaksi.DISETUJUI:
        transaksi.status=TransaksiCOD.StatusTransaksi.SELESAI
        transaksi.completed_at=timezone.now()
        transaksi.save()

        listing=transaksi.listing
        listing.status=StubListing.ListingStatus.TERJUAL
        listing.save()
        messages.success(request, "Transaksi COD selesai! Silahkan beri ulasan.")

    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        context={
            'success':1==1,
            'new_status':'Selesai'
        }
        return JsonResponse(context)
    return redirect('transaksi:detail_transaksi',transaksi_id)

#Ulasan 
@login_required
@require_POST
def submit_ulasan_ajax(request,transaksi_id):
    """
    Create/ Update (For Seller and Buyer): Submit or edit 1-5 rating & review without page reload.
    """
    transaksi = get_object_or_404(TransaksiCOD,id=transaksi_id)
    if request.user not in [transaksi.buyer, transaksi.seller]:
        context ={'success': False,
                   'message': 'Akses ditolak.'
                }
        return JsonResponse(context, status=403)

    if transaksi.status != TransaksiCOD.StatusTransaksi.SELESAI:
        context={'success': False, 
                 'message': 'Transaksi belum selesai.'
                }
        return JsonResponse(context, status=400)

    reviewee = transaksi.seller if request.user == transaksi.buyer else transaksi.buyer
    existing_ulasan = Ulasan.objects.filter(transaksi=transaksi, reviewer=request.user).first()

    form = UlasanForm(request.POST, instance=existing_ulasan)
    if form.is_valid():
        ulasan = form.save(commit=False)
        ulasan.transaksi = transaksi
        ulasan.reviewer = request.user
        ulasan.reviewee = reviewee
        ulasan.save()

        avg_rating = reviewee.ulasan_diterima.aggregate(Avg('rating'))['rating__avg'] or 0
        context= {
            'success': True,
            'message': 'Ulasan berhasil disimpan!',
            'ulasan': {
                'id': str(ulasan.id),
                'rating': ulasan.rating,
                'komentar': ulasan.komentar,
                'reviewer': request.user.username,
                'avg_rating_reviewee': round(avg_rating, 1)
            }
        }
        return JsonResponse(context)
    context = {'success': False, 'errors': form.errors}
    return JsonResponse(context, status=400)
@login_required
@require_POST
def hapus_ulasan(request, ulasan_id):
    """Delete (For Seller and Buyer): Remove a review if it exists and belongs to the user."""
    ulasan = get_object_or_404(Ulasan, id=ulasan_id, reviewer=request.user)
    transaksi_id = ulasan.transaksi.id
    ulasan.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        context={'success': True, 'message': 'Ulasan dihapus.'}
        return JsonResponse(context)
    messages.info(request, "Ulasan Anda telah dihapus.")
    return redirect('transaksi:detail_transaksi', transaksi_id=transaksi_id)

@login_required
def daftar_ulasan(request):
    """READ: List of reviews received by the user (both as buyer and seller)"""
    ulasan_diterima = Ulasan.objects.filter(reviewee=request.user).select_related('reviewer', 'transaksi__listing')
    ulasan_diberikan = Ulasan.objects.filter(reviewer=request.user).select_related('reviewee', 'transaksi__listing')
    avg_rating = ulasan_diterima.aggregate(Avg('rating'))['rating__avg'] or 0.0
    context={
        'ulasan_diterima': ulasan_diterima,
        'ulasan_diberikan': ulasan_diberikan,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'transaksi/daftar_ulasan.html', context)

# Dashboard and Navbar AJAX

def _hitung_dampak_user(user):
    """Helper to calculate saved items, Rupiah, CO2, and Water for a user."""
    selesai_qs = TransaksiCOD.objects.filter(
        Q(buyer=user) | Q(seller=user),
        status=TransaksiCOD.StatusTransaksi.SELESAI
    ).select_related('listing', 'listing__category')

    total_item = selesai_qs.count()
    total_rupiah = sum(t.penghematan_rupiah for t in selesai_qs)
    total_co2 = sum(
        (t.listing.category.co2_saved_per_item_kg if t.listing.category else 0.0)
        for t in selesai_qs
    )
    total_air = sum(
        (t.listing.category.water_saved_per_item_liters if t.listing.category else 0.0)
        for t in selesai_qs
    )

    return {
        'total_item': total_item,
        'total_rupiah': float(total_rupiah),
        'total_co2': round(total_co2, 2),
        'total_air': round(total_air, 2),
    }


@login_required
def dashboard_dampak(request):
    """READ: Personal Environmental Impact Dashboard."""
    dampak = _hitung_dampak_user(request.user)
    return render(request, 'transaksi/dashboard_dampak.html', {'dampak': dampak})


@login_required
def api_dampak_data(request):
    """AJAX: Live-updates numbers on the environmental impact dashboard without reload."""
    return JsonResponse(_hitung_dampak_user(request.user))


@login_required
def api_navbar_counter(request):
    """AJAX: Returns count of incoming pending requests (Pengajuan Masuk) for the navbar badge."""
    count = TransaksiCOD.objects.filter(
        seller=request.user,
        status=TransaksiCOD.StatusTransaksi.DIAJUKAN
    ).count()
    return JsonResponse({'incoming_requests_count': count})