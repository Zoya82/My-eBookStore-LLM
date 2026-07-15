from django.db import transaction
from rest_framework.exceptions import ValidationError, NotFound
from apps.books.models import Book, BookVersion
from .models import Cart

class CartService:
    @staticmethod
    def version_for(item):
        return BookVersion.objects.filter(book=item.book, version_type=item.version_type).first()

    @classmethod
    def invalid_reason(cls, item):
        if not item.book.is_on_sale: return '图书已下架'
        version = cls.version_for(item)
        if not version: return '对应版本不存在'
        if not version.is_on_sale: return '该版本已下架'
        if item.version_type == 'physical' and version.stock < 1: return '纸质版库存不足'
        return ''

    @classmethod
    @transaction.atomic
    def add_to_cart(cls, user, book_id, version_type='physical', quantity=1):
        book = Book.objects.filter(pk=book_id).first()
        if not book: raise ValidationError({'detail': '图书不存在'})
        if not book.is_on_sale: raise ValidationError({'detail': '图书已下架'})
        version = BookVersion.objects.filter(book=book, version_type=version_type).first()
        if not version: raise ValidationError({'detail': '对应版本不存在'})
        if not version.is_on_sale: raise ValidationError({'detail': '该版本已下架'})
        item = Cart.objects.select_for_update().filter(user=user, book=book, version_type=version_type).first()
        new_quantity = (item.quantity if item else 0) + quantity
        if version_type == 'physical' and new_quantity > version.stock:
            raise ValidationError({'detail': f'库存不足，当前版本库存仅 {version.stock} 本'})
        if item:
            item.quantity = new_quantity; item.save(update_fields=['quantity', 'updated_at'])
        else:
            item = Cart.objects.create(user=user, book=book, version_type=version_type, quantity=quantity)
        return item

    @classmethod
    def update_quantity(cls, user, cart_item_id, quantity):
        try: item = Cart.objects.select_related('book').get(id=cart_item_id, user=user)
        except Cart.DoesNotExist: raise NotFound('购物车条目不存在')
        version = cls.version_for(item)
        if not item.book.is_on_sale: raise ValidationError({'detail': '图书已下架'})
        if not version: raise ValidationError({'detail': '对应版本不存在'})
        if not version.is_on_sale: raise ValidationError({'detail': '该版本已下架'})
        if item.version_type == 'physical' and quantity > version.stock:
            raise ValidationError({'detail': f'库存不足，当前版本库存仅 {version.stock} 本'})
        item.quantity = quantity; item.save(update_fields=['quantity', 'updated_at']); return item

    @staticmethod
    def delete_items(user, cart_item_ids): return Cart.objects.filter(user=user, id__in=cart_item_ids).delete()

    @staticmethod
    def toggle_selected(user, cart_item_ids, is_selected): return Cart.objects.filter(user=user, id__in=cart_item_ids).update(is_selected=is_selected)

    @classmethod
    def get_selected_total(cls, user):
        total = 0
        for item in Cart.objects.filter(user=user, is_selected=True).select_related('book'):
            if not cls.invalid_reason(item):
                version = cls.version_for(item)
                total += version.sale_price * item.quantity
        return total

    @classmethod
    def get_invalid_items(cls, user):
        return [item for item in Cart.objects.filter(user=user).select_related('book') if cls.invalid_reason(item)]
