from django.conf import settings
from msgs_app.models import Message


def site_settings(request):
    return {
        'site_name': settings.SITE_NAME,
        'site_description': settings.SITE_DESCRIPTION,
        'site_keywords': settings.SITE_KEYWORDS,
        'site_address': getattr(settings, 'SITE_ADDRESS', ''),
        'site_phone': getattr(settings, 'SITE_PHONE', ''),
        'site_email': getattr(settings, 'SITE_EMAIL', ''),
        'site_working_hours': getattr(settings, 'SITE_WORKING_HOURS', ''),
        'enable_google_auth': settings.ENABLE_GOOGLE_AUTH,
        'enable_favorites': settings.ENABLE_FAVORITES,
    }


def user_theme(request):
    """Expose user's theme preference to all templates."""
    theme = 'system'
    if request.user.is_authenticated:
        try:
            theme = request.user.profile.theme
        except Exception:
            pass
    return {'user_theme': theme}


def unread_messages_count(request):
    """Количество непрочитанных сообщений для текущего пользователя."""
    count = 0
    if request.user.is_authenticated:
        try:
            count = Message.objects.filter(
                recipient=request.user,
                is_read=False,
                is_recipient_deleted=False,
            ).count()
        except Exception:
            pass
    return {'unread_messages_count': count}