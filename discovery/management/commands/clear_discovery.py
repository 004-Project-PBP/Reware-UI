##FOR TESTING PURPOSES

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from discovery.models import (BlockedKeyword, Brand, Category,
                              CuratedCollection, Item, SavedSearch,
                              SearchHistory, WishlistItem)


class Command(BaseCommand):
    help = "Hapus semua data hasil seed_discovery (kategori, brand, item, wishlist, dsb.)."

    def add_arguments(self, parser):
        parser.add_argument("--keep-users", action="store_true",
                            help="Biarkan user demo seller.demo tetap ada")

    def handle(self, *args, **opts):
        WishlistItem.objects.all().delete()
        SavedSearch.objects.all().delete()
        SearchHistory.objects.all().delete()
        CuratedCollection.objects.all().delete() 
        BlockedKeyword.objects.all().delete()
        Item.objects.all().delete()             
        Brand.objects.all().delete()
        Category.objects.all().delete()
        if not opts["keep_users"]:
            get_user_model().objects.filter(username="seller.demo").delete()
        self.stdout.write(self.style.SUCCESS("Semua data discovery telah dihapus."))