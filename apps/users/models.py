from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.utils import avatar_upload_to
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.utils import compress_uploaded_image

class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('person', 'Частное лицо'),
        ('company', 'Компания'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True, verbose_name='Аватар')
    profile_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='person', verbose_name='Тип профиля')
    display_name = models.CharField(max_length=100, blank=True, verbose_name='Отображаемое имя')

    def __str__(self):
        return f'Профиль {self.user.username}'

    def get_display_name(self):
        """Возвращает отображаемое имя, если не пустое, иначе username."""
        if self.display_name and self.display_name.strip():
            return self.display_name.strip()
        return self.user.username

    def get_formatted_phone(self):
        """Возвращает телефон в формате +7 (XXX) XXX-XX-XX, если это возможно."""
        digits = ''.join(filter(str.isdigit, self.phone or ''))
        if len(digits) == 11 and digits[0] == '7':
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        return self.phone


    def save(self, *args, **kwargs):
        if self.pk is not None:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                if old_instance.avatar != self.avatar and self.avatar:
                    compress_uploaded_image(self.avatar, max_dim=850)
            except Profile.DoesNotExist:
                pass
        else:
            if self.avatar:
                compress_uploaded_image(self.avatar, max_dim=850)
        super().save(*args, **kwargs)
 
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
