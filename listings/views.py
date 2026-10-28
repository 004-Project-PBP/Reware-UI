from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
    if new_status in Listing.Status.values:
        listing.status = new_status
        listing.save(update_fields=["status"])
    return redirect("listings:my_listings")