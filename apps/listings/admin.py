from django.contrib import admin
from .models import Listing, ListingImage

def make_active(modeladmin, request, queryset):
    queryset.update(status='active')
    modeladmin.message_user(request, "Выбранные объявления одобрены")
make_active.short_description = "Одобрить выбранные объявления"

def make_inactive(modeladmin, request, queryset):
    queryset.update(status='inactive')
    modeladmin.message_user(request, "Выбранные объявления деактивированы")
make_inactive.short_description = "Деактивировать выбранные объявления"

def make_moderation(modeladmin, request, queryset):
    queryset.update(status='moderation')
    modeladmin.message_user(request, "Выбранные объявления отправлены на модерацию")
make_moderation.short_description = "Отправить на модерацию"

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0
    fields = ('image', 'is_main')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" />'
        return "Нет фото"
    image_preview.allow_tags = True
    image_preview.short_description = 'Превью'

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [ListingImageInline]
    actions = [make_active, make_inactive, make_moderation]

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'price')
        }),
        ('Категория и статус', {
            'fields': ('category', 'status', 'is_promoted')
        }),
        ('Автор', {
            'fields': ('author',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'image_preview', 'is_main')
    list_filter = ('is_main',)
    search_fields = ('listing__title',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="60" />'
        return "Нет"
    image_preview.allow_tags = True
    image_preview.short_description = 'Фото'