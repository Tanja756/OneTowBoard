from django import template
from categories.models import Category

register = template.Library()

@register.inclusion_tag('categories/tree.html')
def show_category_tree(current_category=None):
    categories = Category.objects.filter(parent__isnull=True).order_by('order', 'name').prefetch_related('children')
    expanded_slugs = set()
    if current_category:
        cat = current_category
        while cat:
            if cat.children.exists():
                expanded_slugs.add(cat.slug)
            cat = cat.parent
    return {
        'categories': categories,
        'current_category': current_category,
        'expanded_slugs': expanded_slugs,
    }

@register.inclusion_tag('categories/tree_select.html')
def show_category_tree_select(selected_slug=None):
    categories = Category.objects.filter(parent__isnull=True).order_by('order', 'name').prefetch_related('children')
    return {'categories': categories, 'selected_slug': selected_slug}

@register.simple_tag
def get_category_image(category):
    """Возвращает URL изображения категории или ближайшего родителя с изображением."""
    while category:
        if category.image:
            return category.image.url
        category = category.parent
    return ''