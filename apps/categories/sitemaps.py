from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from categories.models import Category

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse('categories:detail', args=[obj.slug])