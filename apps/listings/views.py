import uuid
import json
import io
import random
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import F, Q
from django.contrib.auth.models import User
from django.conf import settings
from .models import Listing, ListingImage, Favorite
from .forms import ListingForm
from categories.models import Category
import logging
from apps.utils import compress_uploaded_image, log_debug, get_device_template

T = lambda r, t: get_device_template(r, t)
from ratings.models import Rating

logger = logging.getLogger('upload')

def index_view(request):
    view_mode = request.GET.get('view')
    if view_mode:
        request.session['view_mode'] = view_mode
    else:
        view_mode = request.session.get('view_mode', 'grid')

    listings_list = Listing.objects.filter(
        status='active', is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).select_related('author', 'category').prefetch_related('images').order_by('-is_sticky', '-is_urgent', '-created_at')
    paginator = Paginator(listings_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))
    template_name = get_device_template(request, 'listings/index.html')
    return render(request, template_name, {
        'page_obj': page_obj,
        'view_mode': view_mode,
        'favorite_ids': favorite_ids,
    })


def detail_view(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related('author', 'category').prefetch_related('images'),
        pk=pk
    )
    if listing.status != 'active':
        if not request.user.is_authenticated:
            messages.error(request, 'Объявление не найдено.')
            return redirect('listings:index')
        if listing.author != request.user and not request.user.is_staff:
            messages.error(request, 'Объявление не найдено.')
            return redirect('listings:index')
    listing.increment_views(request)
    images = listing.images.all()
    show_contacts = request.user.is_authenticated
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, listing=listing).exists()

    # Счётчики для карточки автора
    author = listing.author
    active_count = Listing.objects.filter(
        author=author, status='active', is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).count()
    completed_count = Listing.objects.filter(
        author=author, is_completed=True
    ).count()

    log_debug(
        "detail_view pk=%s | status=%s | author=%s | active=%d | completed=%d",
        pk, listing.status, author.username, active_count, completed_count,
    )

    # Рейтинг автора
    average_rating = Rating.get_average_for_user(author)
    rating_count = Rating.get_count_for_user(author)
    my_rating = None
    if request.user.is_authenticated:
        my_rating = Rating.get_user_rating(author, request.user)

    context = {
        'listing': listing,
        'images': images,
        'show_contacts': show_contacts,
        'is_completed': listing.is_completed,
        'is_favorite': is_favorite,
        'author_active_count': active_count,
        'author_completed_count': completed_count,
        'average_rating': average_rating,
        'rating_count': rating_count,
        'my_rating': my_rating,
    }
    template_name = get_device_template(request, 'listings/detail.html')
    return render(request, template_name, context)

@login_required
def create_listing_view(request):
    selected_category_slug = request.GET.get('category', '')

    # Генерируем новый токен при каждом GET-запросе
    if request.method == 'GET':
        form_token = str(uuid.uuid4())
        request.session['form_token'] = form_token
        form = ListingForm()
        template_name = get_device_template(request, 'listings/create.html')
        return render(request, template_name, {
            'form': form,
            'selected_category_slug': selected_category_slug,
            'form_token': form_token,
        })

    # POST-запрос
    form = ListingForm(request.POST)
    category_slug = request.POST.get('category_slug')

    # Проверка токена
    client_token = request.POST.get('form_token', '')
    server_token = request.session.get('form_token', '')
    if client_token != server_token:
        messages.error(request, 'Объявление уже отправлено. Пожалуйста, проверьте результат.')
        return redirect('listings:index')

    if not category_slug:
        messages.error(request, 'Пожалуйста, выберите категорию. Фотографии придётся загрузить заново.')
        # Генерируем новый токен, чтобы можно было исправить ошибку
        request.session['form_token'] = str(uuid.uuid4())
        template_name = get_device_template(request, 'listings/create.html')
        return render(request, template_name, {
            'form': form,
            'selected_category_slug': '',
            'form_token': request.session['form_token'],
        })

    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        messages.error(request, 'Выбранная категория не существует.')
        request.session['form_token'] = str(uuid.uuid4())
        template_name = get_device_template(request, 'listings/create.html')
        return render(request, template_name, {
            'form': form,
            'selected_category_slug': '',
            'form_token': request.session['form_token'],
        })

    if form.is_valid():
        listing = form.save(commit=False)
        listing.author = request.user
        listing.category = category
        duration_days = int(form.cleaned_data['duration'])
        listing.expiry_date = date.today() + timedelta(days=duration_days)
        param_data = {}
        for key, value in request.POST.items():
            if key.startswith('param_'):
                slug = key[6:]
                if value:
                    param_data[slug] = value
        listing.parameters = param_data
        listing.save()

        log_debug(
            "create_listing_view: listing pk=%s created | author=%s | category=%s | duration=%d",
            listing.pk, request.user.username, category.slug, duration_days,
        )
    
        images = request.FILES.getlist('images')
        logger.info(f'Начинаю загрузку {len(images)} изображений для объявления {listing.pk}')
    
        try:
            with transaction.atomic():
                for idx, img in enumerate(images, start=1):
                    logger.debug(f'Получен файл: {img.name}, размер: {img.size} байт')
                    if img.size > 10 * 1024 * 1024:
                        raise ValueError(f'Файл {img.name} превышает 10 МБ')
                    listing_image = ListingImage(listing=listing, image=img)
                    listing_image.save()
                    logger.info(f'Изображение {idx} сохранено успешно')
        except IntegrityError as e:
            logger.error(f'Ошибка целостности БД: {e}')
            messages.error(request, 'Не удалось сохранить фотографии. Попробуйте ещё раз.')
            template_name = get_device_template(request, 'listings/create.html')
            return render(request, template_name, {
                'form': form,
                'selected_category_slug': '',
                'form_token': request.session.get('form_token', ''),
            })
        except Exception as e:
            logger.exception(f'Неизвестная ошибка при загрузке изображений: {e}')
            messages.error(request, 'Ошибка при загрузке фотографий.')
            template_name = get_device_template(request, 'listings/create.html')
            return render(request, template_name, {
                'form': form,
                'selected_category_slug': '',
                'form_token': request.session.get('form_token', ''),
            })
    
        # Удаляем токен и завершаем
        if 'form_token' in request.session:
            del request.session['form_token']
            request.session.modified = True
    
        messages.success(request, 'Объявление отправлено на модерацию. Оно появится в ленте после проверки модератором.')
        logger.info(f'Объявление {listing.pk} успешно создано')
        return redirect('listings:index')
    else:
        # Если форма невалидна, генерируем новый токен
        request.session['form_token'] = str(uuid.uuid4())
        template_name = get_device_template(request, 'listings/create.html')
        return render(request, template_name, {
            'form': form,
            'selected_category_slug': '',
            'form_token': request.session['form_token'],
        })

@login_required
def edit_listing_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.author != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав на редактирование этого объявления.')
        return redirect('listings:detail', pk=pk)

    if request.method == 'POST':
        # Проверка токена
        client_token = request.POST.get('form_token', '')
        server_token = request.session.get('form_token', '')
        if client_token != server_token:
            messages.error(request, 'Объявление уже обновлено. Пожалуйста, проверьте результат.')
            return redirect('listings:detail', pk=pk)

        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            listing = form.save(commit=False)
            # Срок публикации
            if 'duration' in form.cleaned_data:
                duration_days = int(form.cleaned_data['duration'])
                listing.expiry_date = date.today() + timedelta(days=duration_days)
            # Параметры категории
            param_data = {}
            for key, value in request.POST.items():
                if key.startswith('param_'):
                    slug = key[6:]
                    if value:
                        param_data[slug] = value
            listing.parameters = param_data
            listing.save()

            # Удаление отмеченных изображений
            delete_ids = request.POST.getlist('delete_images')
            if delete_ids:
                ListingImage.objects.filter(id__in=delete_ids, listing=listing).delete()

            # Новые изображения
            images = request.FILES.getlist('images')
            try:
                with transaction.atomic():
                    for img in images:
                        ListingImage.objects.create(listing=listing, image=img)
            except IntegrityError:
                messages.error(request, 'Не удалось сохранить фотографии. Попробуйте ещё раз.')
                request.session['form_token'] = str(uuid.uuid4())
                template_name = get_device_template(request, 'listings/edit.html')
                return render(request, template_name, {
                    'form': form,
                    'listing': listing,
                    'existing_images': listing.images.all(),
                    'existing_params_json': json.dumps(listing.parameters) if listing.parameters else '{}',
                    'parameters': list(listing.category.get_all_parameters().values()) if listing.category else [],
                    'param_values': listing.parameters or {},
                    'form_token': request.session['form_token'],
                })

            log_debug(
                "edit_listing_view: listing pk=%s updated | author=%s | images=%d",
                listing.pk, request.user.username, len(images),
            )

            # Обновляем токен после успешного сохранения
            request.session['form_token'] = str(uuid.uuid4())
            messages.success(request, 'Объявление обновлено.')
            return redirect('listings:detail', pk=pk)
    else:
        form = ListingForm(instance=listing)

    # Генерируем токен при GET-запросе
    if 'form_token' not in request.session:
        request.session['form_token'] = str(uuid.uuid4())
    form_token = request.session['form_token']

    context = {
        'form': form,
        'listing': listing,
        'existing_images': listing.images.all(),
        'existing_params_json': json.dumps(listing.parameters) if listing.parameters else '{}',
        'parameters': list(listing.category.get_all_parameters().values()) if listing.category else [],
        'param_values': listing.parameters or {},
        'form_token': form_token,
    }
    template_name = get_device_template(request, 'listings/edit.html')
    return render(request, template_name, context)

@login_required
def delete_listing_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.author != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав на удаление этого объявления.')
        return redirect('listings:detail', pk=pk)

    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Объявление удалено.')
        return redirect('users:my_listings')

    template_name = get_device_template(request, 'listings/delete_confirm.html')
    return render(request, template_name, {'listing': listing})


@login_required
def favorite_toggle_view(request, pk):
    """AJAX-эндпоинт: добавить/удалить из избранного. Возвращает JSON."""
    listing = get_object_or_404(Listing, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    return JsonResponse({'is_favorite': is_favorite})


@login_required
def favorite_list_view(request):
    """Список избранных объявлений текущего пользователя."""
    favorites = Favorite.objects.filter(user=request.user).select_related(
        'listing__author', 'listing__category'
    ).prefetch_related('listing__images')
    listings = [fav.listing for fav in favorites]
    template_name = get_device_template(request, 'listings/favorites.html')
    return render(request, template_name, {
        'listings': listings,
    })


@login_required
def complete_listing_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.author != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав на завершение этого объявления.')
        return redirect('listings:detail', pk=pk)

    if request.method == 'POST':
        listing.is_completed = True
        listing.save()
        messages.success(request, 'Объявление завершено.')
        return redirect('users:my_listings')

    template_name = get_device_template(request, 'listings/complete_confirm.html')
    return render(request, template_name, {'listing': listing})


def user_listings_view(request, username):
    """Просмотр всех объявлений определённого пользователя."""
    author = get_object_or_404(User, username=username)
    listings_list = Listing.objects.filter(
        author=author, status='active'
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).select_related('author', 'category').prefetch_related('images').order_by('-created_at')

    paginator = Paginator(listings_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))

    template_name = get_device_template(request, 'listings/index.html')
    return render(request, template_name, {
        'page_obj': page_obj,
        'view_mode': request.session.get('view_mode', 'grid'),
        'favorite_ids': favorite_ids,
        'user_listings_author': author,
    })


def phone_image_view(request, pk):
    """Генерирует PNG-изображение с номером телефона объявления (только для авторизованных)."""
    from PIL import Image, ImageDraw, ImageFont
    listing = get_object_or_404(Listing, pk=pk)
    # Определяем телефон: сначала телефон объявления, иначе телефон автора
    phone = listing.contact_phone.strip() if listing.contact_phone else ''
    if not phone:
        if listing.author.profile.phone:
            phone = listing.author.profile.phone.strip()
    if not phone:
        phone = 'Телефон не указан'

    # Форматируем номер
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and digits[0] == '7':
        formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    else:
        formatted = phone

    # Создаём изображение
    font_size = 16
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Измеряем текст
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), formatted, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    padding_x = 20
    padding_y = 10
    img_w = text_w + padding_x * 2
    img_h = text_h + padding_y * 2

    img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((padding_x, padding_y), formatted, fill=(0, 128, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


