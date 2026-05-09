from django.contrib import admin
from .models import Category, CategoryParameter

class CategoryParameterInline(admin.TabularInline):
    model = CategoryParameter
    extra = 0
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'view_mode', 'order')
    list_editable = ('view_mode', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines = [CategoryParameterInline]
    fields = ('name', 'slug', 'parent', 'image', 'view_mode', 'order')