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
from ratings.models import Rating
from apps.utils import get_device_template

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
    template_name = get_device_template(request, 'users/register.html')
    return render(request, template_name, {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('listings:index')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    username_or_email = user_obj.username
                except User.DoesNotExist:
                    username_or_email = None
            user = authenticate(request, username=username_or_email, password=password) if username_or_email else None
            if user is not None:
                login(request, user)
                messages.success(request, 'Вы вошли в систему.')
                return redirect('listings:index')
            else:
                messages.error(request, 'Неверное имя пользователя (email) или пароль.')
    else:
        form = UserLoginForm()
    template_name = get_device_template(request, 'users/login.html')
    return render(request, template_name, {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли.')
    return redirect('listings:index')

@login_required
def profile_view(request):
    user = request.user
    # Рейтинг пользователя (для отображения)
    profile_rating_avg = Rating.get_average_for_user(user)
    profile_rating_count = Rating.get_count_for_user(user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user.profile)
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
            template_name = get_device_template(request, 'users/profile.html')
            return render(request, template_name, {
                'form': form,
                'email_value': email,
                'phone_value': phone_raw,
                'profile_rating_avg': profile_rating_avg,
                'profile_rating_count': profile_rating_count,
            })
    else:
        form = ProfileForm(instance=user.profile)
        phone_formatted = user.profile.get_formatted_phone()
        template_name = get_device_template(request, 'users/profile.html')
        return render(request, template_name, {
            'form': form,
            'email_value': user.email,
            'phone_value': phone_formatted if phone_formatted else '',
            'profile_rating_avg': profile_rating_avg,
            'profile_rating_count': profile_rating_count,
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

    template_name = get_device_template(request, 'users/my_listings.html')
    return render(request, template_name, {
        'listings': page_obj,
        'status_filter': status_filter,
    })

@login_required
def complete_social_profile_view(request):
    profile = request.user.profile
    need_name = not profile.display_name or not profile.display_name.strip()
    need_phone = not profile.phone or len(''.join(filter(str.isdigit, profile.phone))) != 11
    need_city = not profile.city or not profile.city.strip()

    if request.method == 'POST':
        display_name = request.POST.get('display_name', '').strip()
        phone_raw = request.POST.get('phone', '')
        city = request.POST.get('city', '').strip()

        digits = ''.join(filter(str.isdigit, phone_raw))

        # Валидация телефона (обязателен)
        if len(digits) != 11 or digits[0] != '7':
            messages.error(request, 'Введите корректный номер телефона (+7 (999) 999-99-99).')
            template_name = get_device_template(request, 'users/social_profile_required.html')
            return render(request, template_name, {
                'need_name': need_name,
                'need_phone': need_phone,
                'need_city': need_city,
            })

        if need_name:
            profile.display_name = display_name if display_name else request.user.username

        profile.phone = digits
        profile.city = city
        profile.save()

        # Удаляем флаг из сессии
        if 'require_profile_completion' in request.session:
            del request.session['require_profile_completion']
            request.session.modified = True

        messages.success(request, 'Профиль обновлён!')
        return redirect('listings:index')

    template_name = get_device_template(request, 'users/social_profile_required.html')
    return render(request, template_name, {
        'need_name': need_name,
        'need_phone': need_phone,
        'need_city': need_city,
    })