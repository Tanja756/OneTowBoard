from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Listing

@receiver(post_save, sender=Listing)
def notify_admin_new_listing(sender, instance, created, **kwargs):
    if not (created and getattr(settings, 'NOTIFY_ADMIN_NEW_LISTING', True)):
        return
    subject = f'Новое объявление на {settings.SITE_NAME}'
    message = (
        f'Пользователь {instance.author.username} создал объявление:\n'
        f'Заголовок: {instance.title}\n'
        f'Категория: {instance.category.name if instance.category else "—"}\n'
        f'Ссылка: https://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost"}{instance.get_absolute_url()}\n'
    )
    send_mail(
        subject, message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.TECH_SUPPORT_EMAIL],
        fail_silently=True,
    )