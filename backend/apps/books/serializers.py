#序列化器
from decimal import Decimal

from rest_framework import serializers
from .models import Book, Category, BookVersion


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']

class PublicCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    book_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name', 'book_count']


class BookVersionSerializer(serializers.ModelSerializer):
    """版本序列化器"""
    type_label = serializers.CharField(source='get_version_type_display', read_only=True)

    class Meta:
        model = BookVersion
        fields = ['id', 'version_type', 'type_label', 'price', 'sale_price', 'stock', 'is_on_sale']


class BookListSerializer(serializers.ModelSerializer):
    """图书列表（精简）"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    sale_price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'cover_image', 'sale_price', 'rating', 'sales_count', 'stock', 'category_name']

    def get_sale_price(self, obj):
        sale_price = getattr(obj, 'representative_sale_price', None)
        if sale_price is None:
            return None
        return format(sale_price, '.2f') if isinstance(sale_price, Decimal) else str(sale_price)

    def get_stock(self, obj):
        stock = getattr(obj, 'representative_stock', None)
        if stock is None:
            return None
        return stock


class BookDetailSerializer(serializers.ModelSerializer):
    """图书详情（完整）"""
    category = CategorySerializer(read_only=True)
    versions = BookVersionSerializer(many=True, read_only=True)
    sale_price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    has_preview = serializers.SerializerMethodField()
    has_digital = serializers.SerializerMethodField()
    has_physical = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'

    def get_sale_price(self, obj):
        sale_price = getattr(obj, 'representative_sale_price', None)
        if sale_price is None:
            return None
        return format(sale_price, '.2f') if isinstance(sale_price, Decimal) else str(sale_price)

    def get_stock(self, obj):
        stock = getattr(obj, 'representative_stock', None)
        if stock is None:
            return None
        return stock

    def get_has_preview(self, obj):
        return bool(obj.content_file_path)

    def get_has_digital(self, obj):
        return obj.versions.filter(version_type='digital', is_on_sale=True).exists()

    def get_has_physical(self, obj):
        return obj.versions.filter(version_type='physical', is_on_sale=True).exists()
