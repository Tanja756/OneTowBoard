from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter
def last_seen(value):
    """Форматирует время последней активности.

    Примеры:
      - Если меньше 1 мин: 'только что'
      - Если меньше 1 часа: 'N мин. назад'
      - Если сегодня: 'N ч. назад'
      - Если вчера: 'вчера'
      - Если меньше 7 дней: 'N дн. назад'
      - Иначе: 'был(-а) давно'
    """
    if value is None:
        return ''

    now = timezone.now()
    diff = now - value

    if diff < timedelta(minutes=1):
        return 'только что'
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() // 60)
        return f'{minutes} мин. назад'
    elif diff < timedelta(hours=6):
        hours = int(diff.total_seconds() // 3600)
        return f'{hours} ч. назад'
    elif now.date() == value.date():
        # Сегодня, но больше 6 часов
        hours = int(diff.total_seconds() // 3600)
        return f'{hours} ч. назад'
    elif (now - timedelta(days=1)).date() == value.date():
        return 'вчера'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} дн. назад'
    else:
        return 'был(-а) давно'


@register.filter
def is_online(value):
    """Проверяет, был ли пользователь онлайн в последние 5 минут."""
    if value is None:
        return False
    now = timezone.now()
    return (now - value) < timedelta(minutes=5)