from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    # при смене сортировки убираем page
    if 'sort' in kwargs:
        query.pop('page', None)
    return query.urlencode()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.simple_tag(takes_context=True)
def url_replace_param(context, key, value):
    query = context['request'].GET.copy()
    if value == '':
        query.pop(key, None)
    else:
        query[key] = value
    # сбрасываем страницу при изменении параметра
    query.pop('page', None)
    return query.urlencode()