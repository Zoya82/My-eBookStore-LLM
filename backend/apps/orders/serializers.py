from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    version_label = serializers.CharField(source='get_version_type_display', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id','book_id','book_title','book_cover','book_author','sale_price','quantity','subtotal','version_type','version_label']

class OrderListSerializer(serializers.ModelSerializer):
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id','order_no','status','status_text','total_amount','pay_amount','receiver','receiver_phone','created_at','item_count','items']

class OrderDetailSerializer(serializers.ModelSerializer):
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id','order_no','user','receiver','receiver_phone','receiver_address','remark','total_amount','pay_amount','status','status_text','pay_time','ship_time','receive_time','cancel_time','express_no','express_company','created_at','updated_at','items']
        read_only_fields = fields

class OrderCreateSerializer(serializers.Serializer):
    address = serializers.CharField(required=True, max_length=200, trim_whitespace=True)
    receiver = serializers.CharField(required=True, max_length=50, trim_whitespace=True)
    phone = serializers.CharField(required=True)
    cart_item_ids = serializers.ListField(child=serializers.IntegerField(), required=True, min_length=1)
    remark = serializers.CharField(required=False, allow_blank=True)
    def validate_address(self, value):
        if not value.strip(): raise serializers.ValidationError('收货地址不能为空')
        return value.strip()
    def validate_receiver(self, value):
        if not value.strip(): raise serializers.ValidationError('收货人不能为空')
        return value.strip()
    def validate_phone(self, value):
        if len(value) != 11 or not value.isdigit(): raise serializers.ValidationError('手机号必须为11位数字')
        return value
    def validate_cart_item_ids(self, value):
        if len(set(value)) != len(value): raise serializers.ValidationError('购物车条目 ID 不能重复')
        return value
