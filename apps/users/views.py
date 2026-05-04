from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, UserLoginForm
from listings.models import Listing

def register_view(request):
    if request.user.is_authenticated:
        return redirect('listings:index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('listings:index')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('listings:index')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Вы вошли в систему.')
                return redirect('listings:index')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли.')
    return redirect('listings:index')

@login_required
def profile_view(request):
    """Настройки профиля"""
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.save()
        user.profile.phone = request.POST.get('phone', '')
        user.profile.city = request.POST.get('city', '')
        user.profile.profile_type = request.POST.get('profile_type', 'person')
        avatar = request.FILES.get('avatar')
        if avatar:
            user.profile.avatar = avatar
        user.profile.save()
        messages.success(request, 'Профиль обновлён.')
        return redirect('users:profile')
    return render(request, 'users/profile.html')

@login_required
def my_listings_view(request):
    """Управление объявлениями (Мои объявления)"""
    listings = request.user.listings.prefetch_related('images').order_by('-created_at')
    return render(request, 'users/my_listings.html', {'listings': listings})