from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.cart.models import Cart
from apps.books.models import BookVersion
from .models import Order, OrderItem, DigitalBookPurchase
import uuid

class OrderService:
    @staticmethod
    def generate_order_no(): return f"{timezone.now():%Y%m%d}{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    @transaction.atomic
    def create_order(cls, user, address, receiver, phone, cart_item_ids, remark=''):
        requested = list(cart_item_ids)
        items = list(Cart.objects.select_for_update().select_related('book').filter(user=user, id__in=requested))
        if len(items) != len(requested): raise ValidationError({'detail': '存在无效或不属于当前用户的购物车条目'})
        if any(not item.is_selected for item in items): raise ValidationError({'detail': '所有购物车条目必须已选中'})
        total = Decimal('0.00'); snapshots = []; locked_versions = {}
        for item in items:
            if not item.book.is_on_sale: raise ValidationError({'detail': '图书已下架'})
            version = BookVersion.objects.select_for_update().filter(book=item.book, version_type=item.version_type).first()
            if not version: raise ValidationError({'detail': '对应版本不存在'})
            if not version.is_on_sale: raise ValidationError({'detail': '该版本已下架'})
            if item.version_type == 'physical':
                if version.stock < item.quantity: raise ValidationError({'detail': f'{item.book.title}库存不足'})
                locked_versions[version.pk] = version
            subtotal = version.sale_price * item.quantity; total += subtotal
            snapshots.append(dict(book_id=item.book_id, book_title=item.book.title, book_cover=item.book.cover_image, book_author=item.book.author, sale_price=version.sale_price, quantity=item.quantity, subtotal=subtotal, version_type=item.version_type))
        order = Order.objects.create(order_no=cls.generate_order_no(), user=user, receiver=receiver, receiver_phone=phone, receiver_address=address, total_amount=total, pay_amount=total, status=Order.STATUS_PENDING, remark=remark)
        OrderItem.objects.bulk_create([OrderItem(order=order, **data) for data in snapshots])
        for version in locked_versions.values(): version.stock -= next(x.quantity for x in items if x.version_type == version.version_type and x.book_id == version.book_id); version.save(update_fields=['stock', 'updated_at'])
        Cart.objects.filter(pk__in=[item.pk for item in items], user=user).delete()
        return order

    @classmethod
    @transaction.atomic
    def pay_order(cls, user, order_id):
        order = get_object_or_404(Order, id=order_id, user=user)
        if order.status != Order.STATUS_PENDING: raise ValidationError({'detail': '当前订单状态不允许支付'})
        now = timezone.now(); items = list(order.items.all()); has_physical = any(x.version_type == 'physical' for x in items)
        order.status = Order.STATUS_SUBMITTED if has_physical else Order.STATUS_COMPLETED; order.pay_time = now
        if not has_physical: order.receive_time = now
        order.save(update_fields=['status','pay_time','receive_time','updated_at'])
        for item in items:
            if item.version_type == 'digital': DigitalBookPurchase.objects.get_or_create(user=user, book_id=item.book_id, defaults={'order': order})
        return order

    @classmethod
    @transaction.atomic
    def cancel_order(cls, user, order_id):
        order = get_object_or_404(Order, id=order_id, user=user)
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_SUBMITTED, Order.STATUS_SHIPPED]: raise ValidationError({'detail': '当前订单状态不允许取消'})
        for item in order.items.filter(version_type='physical'):
            version = BookVersion.objects.select_for_update().filter(book_id=item.book_id, version_type='physical').first()
            if version: version.stock += item.quantity; version.save(update_fields=['stock','updated_at'])
        order.status = Order.STATUS_CANCELLED; order.cancel_time = timezone.now(); order.save(update_fields=['status','cancel_time','updated_at']); return order

    @classmethod
    def ship_order(cls, user, order_id, express_no, express_company):
        order = get_object_or_404(Order, id=order_id, user=user)
        if order.status != Order.STATUS_SUBMITTED: raise ValidationError({'detail': '当前订单状态不允许发货'})
        if not order.items.filter(version_type='physical').exists(): raise ValidationError({'detail': '该订单不含纸质版商品'})
        order.status = Order.STATUS_SHIPPED; order.ship_time = timezone.now(); order.express_no = express_no; order.express_company = express_company; order.save(); return order

    @classmethod
    def confirm_receive(cls, user, order_id):
        order = get_object_or_404(Order, id=order_id, user=user)
        if order.status != Order.STATUS_SHIPPED: raise ValidationError({'detail': '当前订单状态不允许确认收货'})
        order.status = Order.STATUS_COMPLETED; order.receive_time = timezone.now(); order.save(); return order
