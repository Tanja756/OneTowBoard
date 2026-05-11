from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import RegisterForm, UserLoginForm, ProfileForm
from listings.models import Listing
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User

@login_required
def resend_verification_email(request):
    user = request.user
    if user.profile.email_verified:
        messages.info(request, 'Ваш email уже подтверждён.')
        return redirect('users:profile')

    # Генерируем новый токен
    user.profile.verification_token = str(uuid.uuid4())
    user.profile.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    from django.urls import reverse
    verification_link = request.build_absolute_uri(reverse('users:verify_email', kwargs={'uidb64': uid, 'token': user.profile.verification_token}))
    send_mail(
        subject=f'Подтверждение email на {settings.SITE_NAME}',
        message=f'Здравствуйте, {user.username}!\n\nДля подтверждения вашего email перейдите по ссылке:\n{verification_link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    messages.success(request, 'Письмо повторно отправлено. Проверьте почту.')
    return redirect('users:profile')

def verify_email_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and user.profile.verification_token == token:
        user.profile.email_verified = True
        user.profile.verification_token = ''
        user.profile.save()
        return render(request, 'users/verify_email_result.html', {'success': True})
    else:
        return render(request, 'users/verify_email_result.html', {'success': False})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('listings:index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Генерируем токен верификации
            profile = user.profile
            profile.verification_token = str(uuid.uuid4())
            profile.save()

            # Формируем ссылку для подтверждения
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            from django.urls import reverse
            verification_link = request.build_absolute_uri(reverse('users:verify_email', kwargs={'uidb64': uid, 'token': profile.verification_token}))
            # Отправляем письмо
            send_mail(
                subject=f'Подтверждение email на {settings.SITE_NAME}',
                message=f'Здравствуйте, {user.username}!\n\nДля подтверждения вашего email перейдите по ссылке:\n{verification_link}\n\nЕсли вы не регистрировались на сайте, проигнорируйте это сообщение.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! На ваш email отправлено письмо для подтверждения.')
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
    status_filter = request.GET.get('status', 'all')
    listings = request.user.listings.prefetch_related('images').order_by('-created_at')

    if status_filter == 'active':
        listings = listings.filter(status='active', is_completed=False)
    elif status_filter == 'moderation':
        listings = listings.filter(status='moderation')
    elif status_filter == 'completed':
        listings = listings.filter(is_completed=True)
    # 'all' — без фильтра

    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/my_listings.html', {
        'listings': page_obj,
        'status_filter': status_filter,
    })
