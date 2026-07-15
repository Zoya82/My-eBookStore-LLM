from django.contrib import admin

# Register your models here.
from .models import Cart

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'quantity', 'is_selected', 'created_at']
    list_filter = ['is_selected']
    search_fields = ['user__username', 'book__title']