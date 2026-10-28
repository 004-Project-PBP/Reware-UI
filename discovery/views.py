import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, ExpressionWrapper, F, FloatField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import (BlockedKeyword, Brand, Category, CuratedCollection, Item,
                     SavedSearch, SearchHistory, WishlistItem)

PAGE_SIZE = 8
SORT_CHOICES = (("terbaru", "Terbaru"), ("termurah", "Termurah"), ("hemat", "Paling Hemat"))
FILTER_KEYS = ("q", "category", "brand", "size", "condition",
               "price_min", "price_max", "retail_min", "retail_max", "cod", "sort")


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"

def read_filters(get_data):
    return {
        "q": get_data.get("q", "").strip(),
        "category": get_data.get("category", "").strip(),
        "brand": get_data.get("brand", "").strip(),
        "size": get_data.get("size", "").strip(),
        "condition": get_data.get("condition", "").strip(),
        "price_min": _int_or_none(get_data.get("price_min")),
        "price_max": _int_or_none(get_data.get("price_max")),
        "retail_min": _int_or_none(get_data.get("retail_min")),
        "retail_max": _int_or_none(get_data.get("retail_max")),
        "cod": get_data.get("cod", "").strip(),
        "sort": get_data.get("sort", "terbaru"),
    }


def apply_filters(qs, f):
    if f["q"] and f["q"].lower() in set(BlockedKeyword.objects.values_list("keyword", flat=True)):
        return qs.none(), True 
    if f["q"]:
        qs = qs.filter(Q(name__icontains=f["q"]) | Q(brand__name__icontains=f["q"])
                       | Q(category__name__icontains=f["q"]))
    if f["category"]:
        qs = qs.filter(category__slug=f["category"])
    if f["brand"]:
        qs = qs.filter(brand__slug=f["brand"])
    if f["size"]:
        qs = qs.filter(size__iexact=f["size"])
    if f["condition"]:
        qs = qs.filter(condition=f["condition"])
    if f["price_min"] is not None:
        qs = qs.filter(price__gte=f["price_min"])
    if f["price_max"] is not None:
        qs = qs.filter(price__lte=f["price_max"])
    if f["retail_min"] is not None:
        qs = qs.filter(retail_price__gte=f["retail_min"])
    if f["retail_max"] is not None:
        qs = qs.filter(retail_price__lte=f["retail_max"])
    if f["cod"]:
        qs = qs.filter(cod_location__icontains=f["cod"])
    return qs, False

def apply_sort(qs, sort):
    if sort == "termurah":
        return qs.order_by("price", "-created_at")
    if sort == "hemat":
        ratio = ExpressionWrapper(
            Case(When(retail_price__gt=0, then=Value(1.0) - (F("price") * 1.0 / F("retail_price"))),
                 default=Value(0.0), output_field=FloatField()),
            output_field=FloatField())
        return qs.annotate(hemat_ratio=ratio).order_by("-hemat_ratio", "-created_at")
    return qs.order_by("-created_at")  # terbaru


def fair_display(items):
    buckets, order = {}, []
    for it in items:
        buckets.setdefault(it.seller_id, []).append(it)
        if len(buckets[it.seller_id]) == 1:
            order.append(it.seller_id)
    out, round_sellers = [], order
    while round_sellers:
        nxt = []
        for sid in round_sellers:
            if buckets[sid]:
                out.append(buckets[sid].pop(0))
            if buckets[sid]:
                nxt.append(sid)
        round_sellers = nxt
    return out


def _catalog_context(request, category=None, brand=None):
    f = read_filters(request.GET)
    if category:
        f["category"] = category.slug
    if brand:
        f["brand"] = brand.slug

    if f["q"] and request.user.is_authenticated and not _is_ajax(request):
        last = request.user.search_history.values_list("keyword", flat=True).first()
        if last != f["q"]:
            SearchHistory.objects.create(user=request.user, keyword=f["q"])

    qs = Item.objects.filter(status="tersedia").select_related("brand", "category", "seller")
    qs, blocked = apply_filters(qs, f)
    items = fair_display(list(apply_sort(qs, f["sort"])))

    page = max(1, _int_or_none(request.GET.get("page")) or 1)
    shown = items[: page * PAGE_SIZE]
    return {
        "categories": Category.objects.annotate(n_items=Count("items", filter=Q(items__status="tersedia"))),
        "category": category, "brand": brand,
        "brands": category.brands.all() if category else Brand.objects.none(),
        "items": shown, "total": len(items),
        "has_next": len(items) > len(shown), "next_page": page + 1,
        "filters": f, "blocked": blocked,
        "sort_choices": SORT_CHOICES, "conditions": Item.CONDITION_CHOICES,
        "sizes": sorted({
            size.strip()
            for size in Item.objects.exclude(size="")
            .values_list("size", flat=True)
            .order_by("size")
            if size and size.strip()
        }),
        "cod_locations": sorted({
            " ".join(location.split())
            for location in Item.objects.exclude(cod_location="")
            .values_list("cod_location", flat=True)
            if location and location.strip()
        }),
        "wishlist_ids": set(request.user.wishlist_items.values_list("item_id", flat=True))
                        if request.user.is_authenticated else set(),
    }

def catalog(request, category_slug=None, brand_slug=None):
    category = get_object_or_404(Category, slug=category_slug) if category_slug else None
    brand = get_object_or_404(Brand, slug=brand_slug) if brand_slug else None
    return render(request, "discovery/catalog.html", _catalog_context(request, category, brand))

def api_catalog(request):
    ctx = _catalog_context(request)
    html = render_to_string("discovery/partial/item_grid.html",
                            {"items": ctx["items"], "wishlist_ids": ctx["wishlist_ids"]},
                            request=request)
    return JsonResponse({"html": html, "total": ctx["total"],
                         "has_next": ctx["has_next"], "next_page": ctx["next_page"],
                         "blocked": ctx["blocked"]})

@login_required
def wishlist_page(request):
    return render(request, "discovery/wishlist.html",
                  {"entries": request.user.wishlist_items.select_related("item", "item__brand")})


@login_required
@require_POST
def api_wishlist_toggle(request):
    item = get_object_or_404(Item, pk=request.POST.get("item_id"))
    entry, created = WishlistItem.objects.get_or_create(buyer=request.user, item=item)
    if not created:
        entry.delete()
    return JsonResponse({"added": created, "count": request.user.wishlist_items.count()})


@login_required
@require_POST
def api_wishlist_note(request, pk):
    entry = get_object_or_404(WishlistItem, pk=pk, buyer=request.user)
    entry.note = request.POST.get("note", "")
    entry.save(update_fields=["note"])
    return JsonResponse({"ok": True})

@login_required
def saved_search_page(request):
    return render(request, "discovery/saved_searches.html",
                  {"saved": request.user.saved_searches.all()})


@login_required
@require_POST
def api_saved_search_create(request):
    if request.POST.get("filters"):
        filters = json.loads(request.POST["filters"])
    else:
        filters = {k: request.POST[k] for k in FILTER_KEYS if request.POST.get(k)}
    SavedSearch.objects.create(
        user=request.user,
        label=request.POST.get("label") or "Pencarian tersimpan",
        keyword=request.POST.get("q", ""),
        filters={k: v for k, v in filters.items() if k in FILTER_KEYS and v},
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_saved_search_update(request, pk):  # update: ubah parameter/label
    ss = get_object_or_404(SavedSearch, pk=pk, user=request.user)
    if request.POST.get("label"):
        ss.label = request.POST["label"]
    if request.POST.get("filters"):
        ss.filters = json.loads(request.POST["filters"])
    if "q" in request.POST:
        ss.keyword = request.POST["q"]
    ss.save()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_saved_search_delete(request, pk):
    get_object_or_404(SavedSearch, pk=pk, user=request.user).delete()
    return JsonResponse({"ok": True})

@login_required
def history_page(request):
    return render(request, "discovery/history.html",
                  {"entries": request.user.search_history.all()[:50]})


@login_required
@require_POST
def api_history_delete(request, pk):
    get_object_or_404(SearchHistory, pk=pk, user=request.user).delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_history_clear(request):
    request.user.search_history.all().delete()
    return JsonResponse({"ok": True})

@login_required
def api_seller_contact(request, pk):
    item = get_object_or_404(Item, pk=pk)
    seller = item.seller
    return JsonResponse({"name": seller.get_full_name() or seller.username, "email": seller.email})

@staff_member_required
def admin_search_stats(request):
    top = SearchHistory.objects.values("keyword").annotate(n=Count("id")).order_by("-n")[:20]
    return render(request, "discovery/admin_stats.html", {
        "top": top,
        "collections": CuratedCollection.objects.all(),
        "blocked": BlockedKeyword.objects.all(),
    })