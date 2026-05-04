import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F
from .models import Listing, ListingImage
from .forms import ListingForm
from categories.models import Category

def index_view(request):
    listings_list = Listing.objects.filter(status='active') \
        .select_related('author', 'category') \
        .prefetch_related('images') \
        .order_by('-created_at')
    paginator = Paginator(listings_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listings/index.html', {'page_obj': page_obj})

def detail_view(request, pk):
    listing = get_object_or_404(Listing.objects.select_related('author', 'category').prefetch_related('images'), pk=pk)
    if listing.status != 'active':
        if not request.user.is_authenticated:
            messages.error(request, 'Объявление не найдено.')
            return redirect('listings:index')
        if listing.author != request.user and not request.user.is_staff:
            messages.error(request, 'Объявление не найдено.')
            return redirect('listings:index')
    images = listing.images.all()
    show_contacts = request.user.is_authenticated
    context = {
        'listing': listing,
        'images': images,
        'show_contacts': show_contacts,
    }
    return render(request, 'listings/detail.html', context)

@login_required
def create_listing_view(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        category_slug = request.POST.get('category_slug')
        if not category_slug:
            messages.error(request, 'Выберите категорию.')
            return render(request, 'listings/create.html', {'form': form})

        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            messages.error(request, 'Выбранная категория не существует.')
            return render(request, 'listings/create.html', {'form': form})

        if form.is_valid():
            all_params = category.get_all_parameters()  # словарь slug -> объект параметра
            param_values = {}
            missing_params = []
            for slug, param_obj in all_params.items():
                value = request.POST.get(f'param_{slug}')
                if value:
                    param_values[slug] = value
                else:
                    missing_params.append(param_obj.name)

            if missing_params:
                messages.error(request, f'Заполните все параметры категории: {", ".join(missing_params)}')
                # Отображаем форму снова, но уже с параметрами
                return render(request, 'listings/create.html', {
                    'form': form,
                    'selected_category_slug': category_slug,
                    'parameters': list(all_params.values()),
                    'param_values': param_values,
                    'missing_params': missing_params,
                })

            # Все параметры заполнены
            listing = form.save(commit=False)
            listing.author = request.user
            listing.category = category
            listing.parameters = param_values
            listing.save()

            images = request.FILES.getlist('images')
            for img in images:
                ListingImage.objects.create(listing=listing, image=img)
            messages.success(request, 'Объявление отправлено на модерацию.')
            return redirect('listings:index')
    else:
        form = ListingForm()

    return render(request, 'listings/create.html', {'form': form})


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

            # Удаляем отмеченные изображения
            delete_ids = request.POST.getlist('delete_images')
            if delete_ids:
                ListingImage.objects.filter(id__in=delete_ids, listing=listing).delete()

            # Сохраняем параметры категории
            all_params = listing.category.get_all_parameters() if listing.category else {}
            param_values = {}
            missing_params = []
            for slug, param_obj in all_params.items():
                value = request.POST.get(f'param_{slug}')
                if value:
                    param_values[slug] = value
                else:
                    missing_params.append(param_obj.name)

            if missing_params:
                messages.error(request, f'Заполните все параметры категории: {", ".join(missing_params)}')
                return render(request, 'listings/edit.html', {
                    'form': form,
                    'listing': listing,
                    'existing_images': listing.images.all(),
                    'existing_params_json': json.dumps(listing.parameters) if listing.parameters else '{}',
                    'parameters': list(all_params.values()),
                    'param_values': param_values,
                    'missing_params': missing_params,
                })

            listing.parameters = param_values
            listing.save()

            # Сохраняем новые изображения
            images = request.FILES.getlist('images')
            for img in images:
                ListingImage.objects.create(listing=listing, image=img)

            messages.success(request, 'Объявление обновлено.')
            return redirect('listings:detail', pk=pk)
    else:
        form = ListingForm(instance=listing)

    category = listing.category
    all_params = category.get_all_parameters() if category else {}
    param_values = listing.parameters or {}

    context = {
        'form': form,
        'listing': listing,
        'existing_images': listing.images.all(),
        'existing_params_json': json.dumps(listing.parameters) if listing.parameters else '{}',
        'parameters': list(all_params.values()),
        'param_values': param_values,
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
        return redirect('listings:index')
    return render(request, 'listings/delete_confirm.html', {'listing': listing})