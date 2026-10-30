from django import template
from ..models import CuratedCollection

register = template.Library()


@register.simple_tag(takes_context=True)
def wishlist_count(context):
    user = context["request"].user
    return user.wishlist_items.count() if user.is_authenticated else 0


@register.inclusion_tag("discovery/partials/curation_home.html")
def pilihan_kampus():
    """Strip kurasi admin untuk ditempel di halaman utama (index.html)."""
    return {"collections": CuratedCollection.objects.filter(active_on_homepage=True)
            .prefetch_related("entries__item")}