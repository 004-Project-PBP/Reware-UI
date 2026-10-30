from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import Http404, JsonResponse

from .forms import ListingForm
from .models import Listing



@login_required
def my_listings(request):
    all_listings = Listing.objects.filter(seller=request.user)
    listings = all_listings
    status = request.GET.get("status")
    if status in Listing.Status.values:
        listings = listings.filter(status=status)
    stats = {
        "total": all_listings.count(),
        "available": all_listings.filter(status=Listing.Status.AVAILABLE).count(),
    }
    return render(request, "listings/my_listings.html", {
        "listings": listings,
        "statuses": Listing.Status.choices,
        "active_status": status,
        "stats": stats,
    })


@login_required
def listing_create(request):
    form = ListingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        listing.seller = request.user
        if request.POST.get("action") == "draft":
            listing.status = Listing.Status.ARCHIVED
        else:
            listing.status = Listing.Status.AVAILABLE
        listing.save()
        return redirect("listings:my_listings")
    return render(request, "listings/listing_form.html", {
        "form": form, "title": "Unggah Item Preloved", "is_create": True,
    })


@login_required
def listing_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    form = ListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listings:my_listings")
    return render(request, "listings/listing_form.html", {
        "form": form, "title": "Edit Item", "is_create": False, "listing": listing,
    })


@login_required
@require_POST
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    listing.delete()
    return redirect("listings:my_listings")


@login_required
@require_POST
def listing_set_status(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    new_status = request.POST.get("status")
    valid = new_status in dict(Listing.Status.choices)
    if valid:
        listing.status = new_status
        listing.save(update_fields=["status"])

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if not valid:
            return JsonResponse({"ok": False, "error": "Status tidak valid"}, status=400)
        mine = Listing.objects.filter(seller=request.user)
        return JsonResponse({
            "ok": True,
            "status": listing.status,
            "label": listing.get_status_display(),
            "total": mine.count(),
            "available": mine.filter(status=Listing.Status.AVAILABLE).count(),
        })
    return redirect("listings:my_listings")

def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    # item yang diarsipkan hanya bisa dilihat pemiliknya
    if listing.status == Listing.Status.ARCHIVED and listing.seller != request.user:
        raise Http404
    return render(request, "listings/listing_detail.html", {"listing": listing})