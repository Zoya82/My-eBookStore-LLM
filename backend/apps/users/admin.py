from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import User, Address


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """自定义用户管理界面"""
    list_display = ['id', 'username', 'phone', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'phone', 'email']
    ordering = ['-date_joined']

    # 在编辑页面显示哪些字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('phone', 'avatar', 'gender', 'email')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

    # 在新增用户时显示的字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone', 'password1', 'password2'),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """收货地址管理界面"""
    list_display = ['id', 'user', 'receiver', 'phone', 'province', 'city', 'district', 'is_default']
    list_filter = ['is_default']
    search_fields = ['user__username', 'receiver', 'phone']