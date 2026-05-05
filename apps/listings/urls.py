from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('create/', views.create_listing_view, name='create'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('<int:pk>/edit/', views.edit_listing_view, name='edit'),
    path('<int:pk>/delete/', views.delete_listing_view, name='delete'),
    path('<int:pk>/complete/', views.complete_listing_view, name='complete'),
]