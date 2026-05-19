from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('create/', views.create_listing_view, name='create'),
    path('favorites/', views.favorite_list_view, name='favorites'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('<int:pk>/edit/', views.edit_listing_view, name='edit'),
    path('<int:pk>/delete/', views.delete_listing_view, name='delete'),
    path('<int:pk>/complete/', views.complete_listing_view, name='complete'),
    path('<int:pk>/favorite-toggle/', views.favorite_toggle_view, name='favorite_toggle'),
    path('<int:pk>/phone-image/', views.phone_image_view, name='phone_image'),
]
