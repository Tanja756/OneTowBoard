from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.list_view, name='list'),
    path('get-parameters/', views.get_parameters_ajax, name='get_parameters'),
    path('<slug:slug>/', views.detail_view, name='detail'),
]