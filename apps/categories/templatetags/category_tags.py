from django import template
from django.template.loader import render_to_string
from categories.models import Category
from apps.utils import get_device_template

register = template.Library()

@register.simple_tag(takes_context=True)
def show_category_tree(context, current_category=None):
    request = context.get('request')
    categories = Category.objects.filter(parent__isnull=True).order_by('order', 'name').prefetch_related('children')
    expanded_slugs = set()
    if current_category:
        cat = current_category
        while cat:
            if cat.children.exists():
                expanded_slugs.add(cat.slug)
            cat = cat.parent
    template_name = get_device_template(request, 'categories/tree.html') if request else 'desktop/categories/tree.html'
    return render_to_string(template_name, {
        'categories': categories,
        'current_category': current_category,
        'expanded_slugs': expanded_slugs,
    })

@register.simple_tag(takes_context=True)
def show_category_tree_select(context, selected_slug=None):
    request = context.get('request')
    categories = Category.objects.filter(parent__isnull=True).order_by('order', 'name').prefetch_related('children')
    template_name = get_device_template(request, 'categories/tree_select.html') if request else 'desktop/categories/tree_select.html'
    return render_to_string(template_name, {'categories': categories, 'selected_slug': selected_slug})

@register.simple_tag
def get_category_image(category):
    """Возвращает URL изображения категории или ближайшего родителя с изображением."""
    while category:
        if category.image:
            return category.image.url
        category = category.parent
    return ''