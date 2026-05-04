from django.urls import path
from . import views

app_name = 'ratings'  # либо соответственно 'users', 'categories', 'ratings', 'search'
urlpatterns = [
    # path('', views.IndexView.as_view(), name='index'),  # добавим позже
]