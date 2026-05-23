import logging
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q

logger = logging.getLogger(__name__)


class ProfileCompletionMiddleware:
    """Middleware, который проверяет, что профиль пользователя заполнен.
    Если нет — перенаправляет на страницу завершения профиля.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/admin/'):
            return self.get_response(request)

        if request.user.is_authenticated:
            if (
                not hasattr(request.user, 'profile') or
                not request.user.profile.phone or
                len(''.join(filter(str.isdigit, request.user.profile.phone))) != 11
            ):
                if (
                    'require_profile_completion' in request.session and
                    path != reverse('users:complete_social_profile')
                ):
                    return redirect('users:complete_social_profile')

        return self.get_response(request)


from users.models import Profile


class LastActivityMiddleware:
    """Middleware, который обновляет last_activity пользователя при каждом запросе."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            try:
                profile = request.user.profile
                now = timezone.now()
                if profile.last_activity is None or (now - profile.last_activity).total_seconds() > 60:
                    Profile.objects.filter(pk=profile.pk).update(last_activity=now)
            except Exception:
                pass
        return self.get_response(request)


class UnreadMessagesMiddleware:
    """Добавляет Django message о непрочитанных сообщениях
    при первом запросе в сессии (один раз за вход)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Не показываем уведомление на странице сообщений
            path = request.path
            if path.startswith('/messages/'):
                return response

            # Показываем уведомление только один раз за сессию
            if not request.session.get('unread_shown', False):
                try:
                    from msgs_app.models import Message
                    count = Message.objects.filter(
                        recipient=request.user,
                        is_read=False,
                        is_recipient_deleted=False,
                    ).count()
                    if count > 0:
                        messages.info(
                            request,
                            f'✉ У вас {count} непрочитанных сообщений.',
                            extra_tags='unread'
                        )
                except Exception:
                    pass
                request.session['unread_shown'] = True

        return response
