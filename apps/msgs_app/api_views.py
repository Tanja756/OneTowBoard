from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Message


@login_required
def unread_count_api(request):
    """Возвращает JSON с количеством непрочитанных сообщений."""
    count = Message.objects.filter(
        recipient=request.user,
        is_read=False,
        is_recipient_deleted=False,
    ).count()
    return JsonResponse({'count': count})