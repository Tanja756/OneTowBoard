import json
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Q
from .models import Listing, ListingImage
from .forms import ListingForm
from categories.models import Category
from datetime import date, timedelta

def index_view(request):
    listings_list = Listing.objects.filter(
        status='active', is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).select_related('author', 'category').prefetch_related('images').order_by('-is_sticky', '-is_urgent', '-created_at')
    paginator = Paginator(listings_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listings/index.html', {'page_obj': page_obj})


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

    if request.method == 'POST':
        form = ListingForm(request.POST)
        category_slug = request.POST.get('category_slug')
        if not category_slug:
            messages.error(request, 'Пожалуйста, выберите категорию. Фотографии придётся загрузить заново.')
            return render(request, 'listings/create.html', {
                'form': form,
                'selected_category_slug': '',
            })

        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            messages.error(request, 'Выбранная категория не существует.')
            return render(request, 'listings/create.html', {
                'form': form,
                'selected_category_slug': '',
            })

        if form.is_valid():
            listing = form.save(commit=False)
            listing.author = request.user
            listing.category = category
            # Вычисляем срок окончания
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

            images = request.FILES.getlist('images')
            for img in images:
                ListingImage.objects.create(listing=listing, image=img)
            messages.success(request, 'Объявление отправлено на модерацию. Оно появится в ленте после проверки модератором.')
            return redirect('listings:index')
    else:
        form = ListingForm()

    return render(request, 'listings/create.html', {
        'form': form,
        'selected_category_slug': selected_category_slug,
    })

@login_required
def edit_listing_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.author != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав на редактирование этого объявления.')
        return redirect('listings:detail', pk=pk)

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            listing = form.save(commit=False)
            # При редактировании срок можно обновлять, добавив поле duration в форму
            # Пока оставляем без изменений
            # Обработка параметров
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
            for img in images:
                ListingImage.objects.create(listing=listing, image=img)
            messages.success(request, 'Объявление обновлено.')
            return redirect('listings:detail', pk=pk)
    else:
        form = ListingForm(instance=listing)

    existing_params = listing.parameters or {}
    context = {
        'form': form,
        'listing': listing,
        'existing_images': listing.images.all(),
        'existing_params_json': json.dumps(existing_params) if existing_params else '{}',
        'parameters': list(listing.category.get_all_parameters().values()) if listing.category else [],
        'param_values': existing_params,
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