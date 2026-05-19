import uuid
from utils import generate_thumbnail
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from apps.utils import listing_image_upload_to, compress_uploaded_image
from categories.models import Category
from datetime import date
import logging
from django.conf import settings
import os

logger = logging.getLogger(__name__)

def default_external_id():
    return uuid.uuid4().hex

class Listing(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активно'),
        ('inactive', 'Неактивно'),
        ('moderation', 'На модерации'),
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    price = models.PositiveIntegerField(blank=True, null=True, verbose_name='Цена')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='moderation', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_promoted = models.BooleanField(default=False, verbose_name='Продвижение')
    is_sticky = models.BooleanField(default=False, verbose_name='Закреплено')
    is_urgent = models.BooleanField(default=False, verbose_name='Срочное')
    is_completed = models.BooleanField(default=False, verbose_name='Завершено')
    expiry_date = models.DateField(blank=True, null=True, verbose_name='Активно до')
    total_views = models.PositiveIntegerField(default=0, verbose_name='Просмотров всего')
    today_views = models.PositiveIntegerField(default=0, verbose_name='Просмотров сегодня')
    last_view_date = models.DateField(blank=True, null=True, verbose_name='Последний просмотр')
    parameters = models.JSONField(default=dict, blank=True, verbose_name='Параметры')
    external_id = models.CharField(
        max_length=50,
        unique=True,
        default=default_external_id,
        verbose_name='Внешний ID',
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Контактный телефон объявления',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

    def __str__(self):
        return self.title

    def get_all_parameters(self):
        return self.category.get_all_parameters() if self.category else {}

    def increment_views(self, request):
        if not request.user.is_authenticated:
            return
        today = date.today()
        already_viewed = self.view_logs.filter(
            user=request.user,
            viewed_at__date=today
        ).exists()
        if not already_viewed:
            if self.last_view_date != today:
                self.today_views = 1
                self.last_view_date = today
            else:
                self.today_views += 1
            self.total_views += 1
            self.save(update_fields=['today_views', 'total_views', 'last_view_date'])
            self.view_logs.create(user=request.user)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('listings:detail', args=[self.pk])

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=listing_image_upload_to, verbose_name='Изображение')
    is_main = models.BooleanField(default=False, verbose_name='Главное')

    @property
    def thumbnail_url(self):
        from apps.utils import generate_thumbnail
        import logging
        logger = logging.getLogger('upload')
        try:
            thumb_rel = generate_thumbnail(self, width=400, height=300)
            if thumb_rel:
                return settings.MEDIA_URL + thumb_rel
            logger.warning(f"Не удалось создать миниатюру для {self.image.path}")
        except Exception as e:
            logger.error(f"Ошибка при создании миниатюры: {e}")
        # Если миниатюры нет — возвращаем оригинал
        return self.image.url

    def __str__(self):
        return f'Фото для {self.listing.title}'

    def save(self, *args, **kwargs):
        try:
            if self.pk is None:
                if self.image:
                    compress_uploaded_image(self.image)
            else:
                try:
                    old = ListingImage.objects.get(pk=self.pk)
                    if old.image != self.image and self.image:
                        compress_uploaded_image(self.image)
                except ListingImage.DoesNotExist:
                    pass
        except Exception as e:
            logger.error(f'Ошибка при сжатии изображения: {e}')
        super().save(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-created_at']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'{self.user.username} → {self.listing.title}'


class ViewLog(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='view_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['listing', 'user', 'viewed_at']),
        ]

    def __str__(self):
        return f'{self.user.username} посмотрел {self.listing.title}'
    
@receiver(pre_delete, sender=ListingImage)
def delete_thumbnail(sender, instance, **kwargs):
    if instance.image:
        # Определяем путь к миниатюре
        base_name = os.path.basename(instance.image.path)
        thumb_name = f'{os.path.splitext(base_name)[0]}_thumb.jpg'
        thumb_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', thumb_name)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)