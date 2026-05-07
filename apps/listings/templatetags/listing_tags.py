from django import template
from django.db.models import Q
from datetime import date
from listings.models import Listing
import random

register = template.Library()

@register.inclusion_tag('listings/recommended_panel.html')
def show_recommended(limit=5):
    promoted = list(Listing.objects.filter(
        is_promoted=True, status='active', is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).select_related('author', 'category').prefetch_related('images'))
    
    random.shuffle(promoted)
    result = promoted[:limit]
    
    if len(result) < limit:
        needed = limit - len(result)
        # добираем обычными активными объявлениями
        others = list(Listing.objects.filter(
            is_promoted=False, status='active', is_completed=False
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
        ).exclude(pk__in=[r.pk for r in result]).select_related('author', 'category').prefetch_related('images'))
        random.shuffle(others)
        result.extend(others[:needed])
    
    return {'recommended': result}