from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order, OrderItem, DigitalBookPurchase


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['book_title', 'sale_price', 'quantity', 'subtotal', 'version_type']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_no', 'user', 'status', 'total_amount', 'receiver', 'created_at']
    list_filter = ['status']
    search_fields = ['order_no', 'user__username', 'receiver']
    readonly_fields = ['order_no', 'created_at']
    inlines = [OrderItemInline]


@admin.register(DigitalBookPurchase)
class DigitalBookPurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'purchased_at']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['purchased_at']