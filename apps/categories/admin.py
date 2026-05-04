from django.contrib import admin
from .models import Category, CategoryParameter

class CategoryParameterInline(admin.TabularInline):
    model = CategoryParameter
    extra = 0
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines = [CategoryParameterInline]