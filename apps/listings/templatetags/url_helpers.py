from django import template
from urllib.parse import urlencode
from decimal import Decimal
from datetime import date

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

@register.filter
def price_display(value):
    """Форматирует цену: 15000 -> '15 000', убирает десятичные знаки."""
    if value is None:
        return '0'
    # Приводим к целому числу
    try:
        int_value = int(round(Decimal(str(value))))
    except (ValueError, TypeError):
        return str(value)
    # Форматируем с пробелами
    result = '{:,}'.format(int_value).replace(',', ' ')
    return result

@register.filter
def days_until(expiry_date):
    """Возвращает срок действия объявления: 'Осталось N дн.' или 'Истекло'."""
    if not expiry_date:
        return ''
    delta = (expiry_date - date.today()).days
    if delta > 0:
        return f'Осталось {delta} дн.'
    else:
        return 'Истекло'

@register.filter
def short_date(d):
    if not d:
        return ''
    today = date.today()
    delta = (today - d.date()).days
    if delta == 0:
        return 'Сегодня'
    elif delta == 1:
        return 'Вчера'
    elif 2 <= delta <= 4:
        return f'{delta} дня назад'
    else:
        return f'{delta} дней назад'