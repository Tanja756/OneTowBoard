from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'score', 'created_at', 'updated_at')
    list_filter = ('score', 'created_at')
    search_fields = ('rater__username', 'rated_user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
