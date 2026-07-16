from rest_framework import serializers
from apps.orders.serializers import OrderItemSerializer
from apps.orders.models import Order
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from apps.books.models import Book, BookVersion, Category
from apps.books.utils import has_readable_content


class AdminOrderListSerializer(serializers.ModelSerializer):
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'user', 'receiver', 'receiver_phone', 'receiver_address',
                  'total_amount', 'pay_amount', 'status', 'status_text', 'created_at',
                  'ship_time', 'express_no', 'express_company', 'items']


class AdminOrderActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['ship', 'cancel'])
    express_no = serializers.CharField(required=False, allow_blank=True, max_length=50, trim_whitespace=True)
    express_company = serializers.CharField(required=False, allow_blank=True, max_length=50, trim_whitespace=True)

    def validate(self, attrs):
        if attrs['action'] == 'ship':
            errors = {}
            if not attrs.get('express_no', '').strip(): errors['express_no'] = ['快递单号不能为空']
            if not attrs.get('express_company', '').strip(): errors['express_company'] = ['快递公司不能为空']
            if errors: raise serializers.ValidationError(errors)
        return attrs


class AdminUserToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)

    def validate(self, attrs):
        extras = set(self.initial_data) - {'is_active'}
        if extras: raise serializers.ValidationError({field: ['不允许修改该字段'] for field in sorted(extras)})
        return attrs


class AdminCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name', 'sort']


class AdminBookVersionSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source='get_version_type_display', read_only=True)
    class Meta:
        model = BookVersion
        fields = ['id', 'version_type', 'type_label', 'price', 'sale_price', 'stock', 'is_on_sale']


class AdminBookReadSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    versions = AdminBookVersionSerializer(many=True, read_only=True)
    has_content = serializers.BooleanField(read_only=True)
    content_available = serializers.SerializerMethodField()
    content_file_path = serializers.SerializerMethodField()
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'publish_date', 'cover_image', 'description', 'catalog', 'content_file_path', 'category', 'category_name', 'is_on_sale', 'sales_count', 'rating', 'on_shelf_date', 'created_at', 'updated_at', 'has_content', 'content_available', 'versions']
    def get_content_available(self, obj): return has_readable_content(obj)
    def get_content_file_path(self, obj):
        value = obj.content_file_path
        if not value: return value
        path = Path(value)
        return value if not path.is_absolute() and '..' not in path.parts and not (len(value) > 1 and value[1] == ':') and not value.startswith(('\\\\', '/\\')) else None


class AdminBookVersionWriteSerializer(serializers.Serializer):
    version_type = serializers.ChoiceField(choices=['digital', 'physical'])
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    sale_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    stock = serializers.IntegerField(min_value=0)
    is_on_sale = serializers.BooleanField()
    def validate(self, attrs):
        if attrs['sale_price'] > attrs['price']: raise serializers.ValidationError({'sale_price': ['销售价不能高于定价']})
        return attrs


class AdminBookWriteSerializer(serializers.ModelSerializer):
    versions = AdminBookVersionWriteSerializer(many=True, required=False)
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'publish_date', 'cover_image', 'description', 'catalog', 'content_file_path', 'category', 'is_on_sale', 'on_shelf_date', 'versions']
        extra_kwargs = {name: {'required': False, 'allow_null': True} for name in ['publish_date', 'cover_image', 'description', 'catalog', 'content_file_path', 'category', 'on_shelf_date']}
        extra_kwargs['isbn'] = {'validators': []}
    def validate_title(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('书名不能为空')
        return value
    def validate_author(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('作者不能为空')
        return value
    def validate_isbn(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('ISBN 不能为空')
        qs = Book.objects.filter(isbn=value)
        if self.instance: qs = qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError('ISBN 已存在')
        return value
    def validate_publisher(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('出版社不能为空')
        return value
    def validate_cover_image(self, value):
        if not value: return value
        value = value.strip()
        if any(ord(char) < 32 for char in value) or '..' in value or value.lower().startswith(('javascript:', 'data:', 'file:')) or value.startswith(('\\\\', '/\\')) or (len(value) > 1 and value[1] == ':'): raise serializers.ValidationError('封面路径不安全')
        if value.startswith(('http://', 'https://', '/media/', 'media/')): return value
        raise serializers.ValidationError('封面路径不安全')
    def validate_content_file_path(self, value):
        if not value: return value
        value = value.strip(); relative = Path(value); root = Path(settings.MEDIA_ROOT).resolve()
        try: path = (root / relative).resolve()
        except OSError: path = None
        if relative.is_absolute() or '..' in relative.parts or (len(value) > 1 and value[1] == ':') or value.startswith(('\\\\', '/\\')) or not path or (path != root and root not in path.parents) or not path.is_file(): raise serializers.ValidationError('正文文件不可用')
        try:
            if path.stat().st_size <= 0 or not path.read_text(encoding='utf-8-sig'): raise serializers.ValidationError('正文文件不可用')
        except (OSError, UnicodeError): raise serializers.ValidationError('正文文件不可用')
        return value
    def validate_versions(self, value):
        kinds = [item['version_type'] for item in value]
        if len(kinds) != len(set(kinds)): raise serializers.ValidationError('版本类型不能重复')
        return value
    def validate(self, attrs):
        allowed = set(self.fields)
        extras = set(self.initial_data) - allowed
        if extras: raise serializers.ValidationError({field: ['不允许修改该字段'] for field in sorted(extras)})
        if self.instance is None and 'is_on_sale' not in attrs: raise serializers.ValidationError({'is_on_sale': ['该字段为必填项']})
        if self.instance is None and not attrs.get('versions'): raise serializers.ValidationError({'versions': ['至少需要一个版本']})
        return attrs


class AdminBookSaleSerializer(serializers.Serializer):
    is_on_sale = serializers.BooleanField()
    def validate(self, attrs):
        extras = set(self.initial_data) - {'is_on_sale'}
        if extras: raise serializers.ValidationError({field: ['不允许修改该字段'] for field in sorted(extras)})
        return attrs


class AdminRecentOrderSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    pay_amount = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id', 'order_no', 'username', 'receiver', 'status', 'status_text', 'pay_amount', 'created_at']
    def get_username(self, obj): return getattr(obj.user, 'username', '') or ''
    def get_pay_amount(self, obj): return format(obj.pay_amount or Decimal('0'), '.2f')
