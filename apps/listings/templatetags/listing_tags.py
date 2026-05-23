from django import template
from django.template.loader import render_to_string
from django.db.models import Q
from datetime import date
from listings.models import Listing
import random
from apps.utils import get_device_template

register = template.Library()

@register.simple_tag(takes_context=True)
def show_recommended(context, limit=5):
    request = context.get('request')
    promoted = list(Listing.objects.filter(
        is_promoted=True, status='active', is_completed=False
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
    ).select_related('author', 'category').prefetch_related('images'))
    
    random.shuffle(promoted)
    result = promoted[:limit]
    
    if len(result) < limit:
        needed = limit - len(result)
        others = list(Listing.objects.filter(
            is_promoted=False, status='active', is_completed=False
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=date.today())
        ).exclude(pk__in=[r.pk for r in result]).select_related('author', 'category').prefetch_related('images'))
        random.shuffle(others)
        result.extend(others[:needed])
    
    template_name = get_device_template(request, 'listings/recommended_panel.html') if request else 'desktop/listings/recommended_panel.html'
    return render_to_string(template_name, {'recommended': result})
