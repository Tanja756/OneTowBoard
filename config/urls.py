from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps import views as sitemap_views
from apps.listings.sitemaps import ListingSitemap
from apps.categories.sitemaps import CategorySitemap
from config.sitemaps import StaticSitemap

sitemaps = {
    'listings': ListingSitemap,
    'categories': CategorySitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('listings.urls')),
    path('users/', include('users.urls')),  # авторизация, регистрация, профиль
    path('categories/', include('categories.urls')),
    path('ratings/', include('ratings.urls')),
    path('search/', include('search.urls')),
    path('messages/', include('msgs_app.urls')),
    path('sitemap.xml', sitemap_views.index, {'sitemaps': sitemaps, 'sitemap_url_name': 'sitemaps'}),
    path('sitemaps-<section>.xml', sitemap_views.sitemap, {'sitemaps': sitemaps}, name='sitemaps'),
]

if settings.ENABLE_GOOGLE_AUTH:
    urlpatterns.append(path('accounts/', include('allauth.urls')))
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)