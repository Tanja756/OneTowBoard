from django.core.management.base import BaseCommand
from datetime import date
from apps.listings.models import Listing

class Command(BaseCommand):
    help = 'Завершает объявления, у которых истёк срок'

    def handle(self, *args, **options):
        expired = Listing.objects.filter(
            is_completed=False,
            expiry_date__isnull=False,
            expiry_date__lt=date.today()
        )
        count = expired.update(is_completed=True)
        self.stdout.write(self.style.SUCCESS(f'Завершено объявлений: {count}'))