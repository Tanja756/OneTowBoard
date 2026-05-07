from django.core.paginator import Paginator
from django.db.models import Q, F
from django.db.models.functions import Lower
from django.shortcuts import render
from datetime import date
from listings.models import Listing
from categories.models import Category

def search_view(request):
    query = request.GET.get('q', '')
    results = Listing.objects.filter(status='active', is_completed=False).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    )

    # Фильтрация по выбранной категории (если есть)
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            cat = Category.objects.get(slug=category_slug)
            # Получаем id самой категории и всех потомков
            cat_ids = cat.get_descendants_ids(include_self=True)
            results = results.filter(category_id__in=cat_ids)
        except Category.DoesNotExist:
            pass  # если категория не найдена, просто игнорируем

    if query:
        # Приводим и поле, и запрос к нижнему регистру для полной независимости от регистра
        results = results.annotate(
            title_lower=Lower('title'),
            description_lower=Lower('description')
        ).filter(
            Q(title_lower__contains=query.lower()) | Q(description_lower__contains=query.lower())
        )

    # Фильтры
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    no_price = request.GET.get('no_price') == '1'

    if no_price:
        results = results.filter(price__isnull=True)
    else:
        if price_from:
            results = results.filter(price__gte=price_from)
        if price_to:
            results = results.filter(price__lte=price_to)

    # Сортировка
    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'cheapest': F('price').asc(nulls_last=True),
        'expensive': F('price').desc(nulls_last=True),
    }
    ordering = sort_options.get(sort, '-created_at')

    results = results.order_by('-is_sticky', '-is_urgent', ordering).prefetch_related('images').select_related('author', 'category')

    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'search/search.html', {
        'query': query,
        'page_obj': page_obj,
        'sort': sort,
        'price_from': price_from or '',
        'price_to': price_to or '',
        'no_price': no_price,
    })