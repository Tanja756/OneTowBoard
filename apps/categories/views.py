from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from datetime import date
from .models import Category
from listings.models import Listing


def list_view(request):
    categories = Category.objects.filter(parent__isnull=True)  # только корневые
    return render(request, 'categories/list.html', {'categories': categories})

def get_parameters_ajax(request):
    """Возвращает HTML с полями для параметров выбранной категории."""
    category_slug = request.GET.get('category_slug')
    if not category_slug:
        return JsonResponse({'html': ''})

    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return JsonResponse({'html': '<p class="text-danger">Категория не найдена</p>'})

    # Рекурсивный сбор параметров с учётом наследования
    def get_all_parameters(cat):
        params_dict = {}
        if cat.parent:
            params_dict.update(get_all_parameters(cat.parent))
        for p in cat.parameters.all():
            params_dict[p.slug] = p
        return params_dict

    parameters = list(get_all_parameters(category).values())
    html = render_to_string('categories/parameters_form.html', {'parameters': parameters})
    return JsonResponse({'html': html})


def detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    # Получаем ID текущей категории и всех её потомков
    category_ids = category.get_descendants_ids(include_self=True)
    category = get_object_or_404(Category, slug=slug)
    
    view_mode = request.GET.get('view', category.view_mode if category.view_mode else 'grid')

    # Базовый queryset с фильтрацией по сроку и незавершённости
    listings = Listing.objects.filter(
        category_id__in=category_ids,
        status='active',
        is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    )

    # Фильтры цены
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    no_price = request.GET.get('no_price') == '1'

    if no_price:
        listings = listings.filter(price__isnull=True)
    else:
        if price_from:
            listings = listings.filter(price__gte=price_from)
        if price_to:
            listings = listings.filter(price__lte=price_to)

    # Сортировка (сначала закреплённые, потом по выбранному критерию)
    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'cheapest': F('price').asc(nulls_last=True),
        'expensive': F('price').desc(nulls_last=True),
    }
    ordering = sort_options.get(sort, '-created_at')
    listings = listings.order_by('-is_sticky', '-is_urgent', ordering).prefetch_related('images').select_related('author', 'category')

    # Наследование параметров от родительских категорий
    def get_all_parameters(cat):
        params_dict = {}
        if cat.parent:
            params_dict.update(get_all_parameters(cat.parent))
        for p in cat.parameters.all():
            params_dict[p.slug] = p
        return params_dict

    parameters = list(get_all_parameters(category).values())
    selected_params = {p.slug: request.GET.get(p.slug) for p in parameters}

    # Фильтрация по параметрам категории
    for param in parameters:
        value = request.GET.get(param.slug)
        if value:
            listings = listings.filter(**{f'parameters__{param.slug}': value})

    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'categories/detail.html', {
        'category': category,
        'view_mode': view_mode,
        'page_obj': page_obj,
        'sort': sort,
        'price_from': price_from or '',
        'price_to': price_to or '',
        'no_price': no_price,
        'parameters': parameters,
        'selected_params': selected_params,
    })