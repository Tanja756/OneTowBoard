from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('api/<str:username>/', views.get_rating_view, name='get_rating'),
    path('api/<str:username>/rate/', views.rate_user_view, name='rate_user'),
]