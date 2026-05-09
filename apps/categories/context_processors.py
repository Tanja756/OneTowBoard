from .models import Category

def categories_processor(request):
    return {
        'all_categories': Category.objects.filter(parent__isnull=True).order_by('order', 'name')
    }