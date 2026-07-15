from rest_framework import serializers
from apps.orders.serializers import OrderItemSerializer
from apps.orders.models import Order


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
