from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.utils.html import escape
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(post_save, sender=User)
def notify_admin_new_user(sender, instance, created, **kwargs):
    if not (created and getattr(settings, 'NOTIFY_ADMIN_NEW_USER', True)):
        return
    subject = f'Новый пользователь на {escape(settings.SITE_NAME)}'
    message = (
        f'Зарегистрирован новый пользователь:\n'
        f'Имя пользователя: {escape(instance.username)}\n'
        f'Email: {escape(instance.email)}\n'
        f'Дата регистрации: {instance.date_joined.strftime("%d.%m.%Y %H:%M")}\n'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.TECH_SUPPORT_EMAIL],
        fail_silently=True,
    )

@receiver(user_logged_in)
def check_profile_completeness(sender, request, user, **kwargs):
    if not hasattr(user, 'profile'):
        return
    profile = user.profile
    need_name = not profile.display_name or not profile.display_name.strip()
    need_phone = not profile.phone or len(''.join(filter(str.isdigit, profile.phone))) != 11
    need_city = not profile.city or not profile.city.strip()
    if need_name or need_phone or need_city:
        request.session['require_profile_completion'] = True