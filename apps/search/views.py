from django.core.paginator import Paginator
from django.db.models import Q, F
from django.shortcuts import render
from listings.models import Listing

def search_view(request):
    query = request.GET.get('q', '')
    results = Listing.objects.filter(status='active', is_completed=False)
    if query:
        results = results.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
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
    results = results.order_by(ordering).prefetch_related('images').select_related('author', 'category')

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