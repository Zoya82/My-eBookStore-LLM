from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from apps.books.models import Book
from apps.orders.models import Order, OrderItem, DigitalBookPurchase
from .models import Review, Favorite, BrowsingHistory

class InteractionService:
    @staticmethod
    def completed_purchase(user, book_id):
        return OrderItem.objects.filter(order__user=user, order__status=Order.STATUS_COMPLETED, book_id=book_id).exists()

    @classmethod
    @transaction.atomic
    def create_review(cls, user, book_id, rating, comment=''):
        book = get_object_or_404(Book, pk=book_id)
        if not cls.completed_purchase(user, book_id): raise ValidationError({'detail': '尚未购买该书或订单未完成，无法评价'})
        if Review.objects.filter(user=user, book=book).exists(): raise ValidationError({'detail': '您已经评价过这本书'})
        review = Review.objects.create(user=user, book=book, rating=rating, comment=comment)
        book.rating = Review.objects.filter(book=book).aggregate(avg=Avg('rating'))['avg'] or 0
        book.save(update_fields=['rating'])
        return review

    @classmethod
    @transaction.atomic
    def toggle_favorite(cls, user, book_id):
        book = get_object_or_404(Book, pk=book_id)
        favorite = Favorite.objects.select_for_update().filter(user=user, book=book).first()
        if favorite:
            favorite.delete(); return {'action':'removed','book_id':book_id,'is_favorite':False}
        if not book.is_on_sale: raise ValidationError({'detail':'下架图书不能新增收藏'})
        Favorite.objects.create(user=user, book=book)
        return {'action':'added','book_id':book_id,'is_favorite':True}

    @classmethod
    @transaction.atomic
    def add_browsing_history(cls, user, book_id):
        book = get_object_or_404(Book, pk=book_id)
        if not book.is_on_sale and not DigitalBookPurchase.objects.filter(user=user, book=book).exists(): raise ValidationError({'detail':'无权记录该下架图书历史'})
        BrowsingHistory.objects.filter(user=user, book=book).delete()
        history = BrowsingHistory.objects.create(user=user, book=book)
        ids = list(BrowsingHistory.objects.filter(user=user).order_by('-created_at','-id').values_list('id', flat=True)[20:])
        if ids: BrowsingHistory.objects.filter(user=user, id__in=ids).delete()
        return history

    @staticmethod
    def clear_browsing_history(user): return BrowsingHistory.objects.filter(user=user).delete()[0]
