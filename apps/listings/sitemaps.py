from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from listings.models import Listing

class ListingSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Listing.objects.filter(status='active', is_completed=False)

    def lastmod(self, obj):
        return obj.updated_at   # или created_at

    def location(self, obj):
        return reverse('listings:detail', args=[obj.pk])