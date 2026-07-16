from django.contrib import admin

# Register your models here.
from .models import Review, Favorite, BrowsingHistory


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'rating', 'comment_preview', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__username', 'book__title']

    def comment_preview(self, obj):
        return obj.comment[:30] + '...' if obj.comment and len(obj.comment) > 30 else obj.comment
    comment_preview.short_description = '评价内容（预览）'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'created_at']
    search_fields = ['user__username', 'book__title']


@admin.register(BrowsingHistory)
class BrowsingHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'created_at']
    search_fields = ['user__username', 'book__title']