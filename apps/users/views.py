from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, UserLoginForm, ProfileForm
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
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        # Ручная валидация email и телефона
        email = request.POST.get('email', '').strip()
        phone_raw = request.POST.get('phone', '')
        digits = ''.join(filter(str.isdigit, phone_raw))
        phone_valid = len(digits) == 11 and digits[0] == '7'

        if not email:
            form.add_error(None, 'Email обязателен.')
        if not phone_valid:
            form.add_error(None, 'Введите корректный номер телефона (+7 (999) 999-99-99).')

        if form.is_valid() and email and phone_valid:
            user = request.user
            user.email = email
            user.save()
            profile = form.save(commit=False)
            profile.phone = digits
            profile.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('users:profile')
        else:
            # Передаём телефон и email в шаблон, чтобы сохранить введённые значения
            return render(request, 'users/profile.html', {
                'form': form,
                'email_value': email,
                'phone_value': phone_raw,
            })
    else:
        form = ProfileForm(instance=request.user.profile)
        phone_formatted = request.user.profile.get_formatted_phone()
        return render(request, 'users/profile.html', {
            'form': form,
            'email_value': request.user.email,
            'phone_value': phone_formatted if phone_formatted else '',
        })

@login_required
def my_listings_view(request):
    """Управление объявлениями (Мои объявления)"""
    listings = request.user.listings.prefetch_related('images').order_by('-created_at')
    return render(request, 'users/my_listings.html', {'listings': listings})