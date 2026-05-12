from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('listings.urls')),
    path('users/', include('users.urls')),  # авторизация, регистрация, профиль
    path('categories/', include('categories.urls')),
    path('ratings/', include('ratings.urls')),
    path('search/', include('search.urls')),
]

if settings.ENABLE_GOOGLE_AUTH:
    urlpatterns.append(path('accounts/', include('allauth.urls')))
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)