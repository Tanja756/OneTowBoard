import uuid
import json
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import F, Q
from .models import Listing, ListingImage
from .forms import ListingForm
from categories.models import Category
from datetime import date, timedelta
import logging
from apps.utils import compress_uploaded_image

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
    return render(request, 'listings/index.html', {
        'page_obj': page_obj,
        'view_mode': view_mode,
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
    context = {
        'listing': listing,
        'images': images,
        'show_contacts': show_contacts,
        'is_completed': listing.is_completed,
    }
    return render(request, 'listings/detail.html', context)

@login_required
def create_listing_view(request):
    selected_category_slug = request.GET.get('category', '')

    # Генерируем новый токен при каждом GET-запросе
    if request.method == 'GET':
        form_token = str(uuid.uuid4())
        request.session['form_token'] = form_token
        form = ListingForm()
        return render(request, 'listings/create.html', {
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
        return render(request, 'listings/create.html', {
            'form': form,
            'selected_category_slug': '',
            'form_token': request.session['form_token'],
        })

    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        messages.error(request, 'Выбранная категория не существует.')
        request.session['form_token'] = str(uuid.uuid4())
        return render(request, 'listings/create.html', {
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
            return render(request, 'listings/create.html', {
                'form': form,
                'selected_category_slug': '',
                'form_token': request.session.get('form_token', ''),
            })
        except Exception as e:
            logger.exception(f'Неизвестная ошибка при загрузке изображений: {e}')
            messages.error(request, 'Ошибка при загрузке фотографий.')
            return render(request, 'listings/create.html', {
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
        return render(request, 'listings/create.html', {
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
                return render(request, 'listings/edit.html', {
                    'form': form,
                    'listing': listing,
                    'existing_images': listing.images.all(),
                    'existing_params_json': json.dumps(listing.parameters) if listing.parameters else '{}',
                    'parameters': list(listing.category.get_all_parameters().values()) if listing.category else [],
                    'param_values': listing.parameters or {},
                    'form_token': request.session['form_token'],
                })

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
    return render(request, 'listings/edit.html', context)

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

    return render(request, 'listings/delete_confirm.html', {'listing': listing})


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

    return render(request, 'listings/complete_confirm.html', {'listing': listing})