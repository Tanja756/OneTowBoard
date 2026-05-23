from django.db import models
from django.contrib.auth.models import User
from listings.models import Listing


class Message(models.Model):
    """Сообщение от пользователя автору объявления (или ответ)."""
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='messages',
        verbose_name='Объявление'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages',
        verbose_name='Отправитель'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages',
        verbose_name='Получатель'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='replies', verbose_name='Ответ на'
    )
    text = models.TextField(verbose_name='Текст сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Прочитано в')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    is_sender_deleted = models.BooleanField(default=False, verbose_name='Удалено отправителем')
    is_recipient_deleted = models.BooleanField(default=False, verbose_name='Удалено получателем')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['listing', 'parent']),
        ]

    def __str__(self):
        return f'От {self.sender.username} к {self.recipient.username} — {self.listing.title[:30]}'