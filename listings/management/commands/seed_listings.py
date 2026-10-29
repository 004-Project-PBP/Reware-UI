from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SEED_SELLERS = ["seed_ayu", "seed_bima", "seed_citra"]


class Command(BaseCommand):
    help = "Isi database dengan data contoh listing (seed/demo)."

    def handle(self, *args, **options):
        sellers = []
        for username in SEED_SELLERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("seedpass123")
                user.save()
            sellers.append(user)
        self.stdout.write(self.style.SUCCESS(f"{len(sellers)} seller siap dipakai."))