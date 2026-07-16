from rest_framework import serializers
from .models import Cart
from apps.books.serializers import BookListSerializer
from .services import CartService

class CartSerializer(serializers.ModelSerializer):
    book_detail = BookListSerializer(source='book', read_only=True)
    version_type = serializers.CharField(read_only=True)
    version_label = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    invalid_reason = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ['id','book','book_detail','version_type','version_label','quantity','is_selected','unit_price','subtotal','stock','is_valid','invalid_reason','created_at']
        read_only_fields = ['user','book']
    def get_version(self, obj): return CartService.version_for(obj)
    def get_version_label(self, obj): return obj.get_version_type_display()
    def get_unit_price(self, obj):
        version = self.get_version(obj)
        return f'{version.sale_price:.2f}' if version else '0.00'
    def get_subtotal(self, obj):
        version = self.get_version(obj)
        return f'{version.sale_price * obj.quantity:.2f}' if version else '0.00'
    def get_stock(self, obj):
        version = self.get_version(obj)
        return version.stock if version else 0
    def get_invalid_reason(self, obj): return CartService.invalid_reason(obj)
    def get_is_valid(self, obj): return not CartService.invalid_reason(obj)

class CartAddSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(required=True)
    version_type = serializers.ChoiceField(choices=['digital','physical'], required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1)
