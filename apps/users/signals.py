from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.utils.html import escape

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