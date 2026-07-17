from django.contrib import admin

# Register your models here.
from .models import Book, Category, BookVersion


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'sort', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']


class BookVersionInline(admin.TabularInline):
    """在图书后台内联显示版本信息"""
    model = BookVersion
    extra = 1
    fields = ['version_type', 'price', 'sale_price', 'stock', 'is_on_sale']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'is_on_sale', 'on_shelf_date', 'has_preview']
    list_filter = ['is_on_sale', 'category']
    search_fields = ['title', 'author', 'isbn']
    inlines = [BookVersionInline]

    def has_preview(self, obj):
        """是否有试读内容"""
        return bool(obj.content_file_path)
    has_preview.short_description = '试读'
    has_preview.boolean = True
