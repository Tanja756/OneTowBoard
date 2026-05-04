from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'profile_type', 'avatar_preview')
    list_filter = ('profile_type',)

    def avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="40" style="border-radius: 50%;" />'
        return "Нет"
    avatar_preview.allow_tags = True
    avatar_preview.short_description = 'Аватар'