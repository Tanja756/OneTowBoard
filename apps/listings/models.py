from django.db import models
from django.contrib.auth.models import User
from categories.models import Category

class Listing(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активно'),
        ('inactive', 'Неактивно'),
        ('moderation', 'На модерации'),
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Цена')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='moderation', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_promoted = models.BooleanField(default=False, verbose_name='Продвижение')
    parameters = models.JSONField(default=dict, blank=True, verbose_name='Параметры')
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/', verbose_name='Изображение')
    is_main = models.BooleanField(default=False, verbose_name='Главное')

    def __str__(self):
        return f'Фото для {self.listing.title}'