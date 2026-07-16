from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.books.models import Book
from apps.orders.models import Order, OrderItem, DigitalBookPurchase
from .models import Review, Favorite, BrowsingHistory

User=get_user_model()
class InteractionContractTests(TestCase):
    def setUp(self):
        self.client=APIClient();self.user=User.objects.create_user(username='intuser',phone='13910000001',password='knownpass');self.other=User.objects.create_user(username='otherint',phone='13910000002',password='knownpass');self.book=Book.objects.create(title='互动书',author='作者',isbn='int-isbn',publisher='出版社',is_on_sale=True);self.book2=Book.objects.create(title='互动书2',author='作者',isbn='int-isbn2',publisher='出版社',is_on_sale=True);self.off=Book.objects.create(title='下架书',author='作者',isbn='int-isbn3',publisher='出版社',is_on_sale=False);self.client.force_authenticate(self.user);self.url='/api/interactions/'
    def order(self,user=None,status=Order.STATUS_COMPLETED,book=None):
        o=Order.objects.create(order_no=f'INT{Order.objects.count()+1:07d}',user=user or self.user,receiver='x',receiver_phone='13900000000',receiver_address='x',total_amount=1,pay_amount=1,status=status);OrderItem.objects.create(order=o,book_id=(book or self.book).id,book_title=(book or self.book).title,book_cover='',book_author='作者',sale_price=Decimal('1'),quantity=1,subtotal=Decimal('1'),version_type='digital');return o
    def test_review_validation_permission_and_average(self):
        self.client.force_authenticate(None);self.assertEqual(self.client.get(self.url+'reviews/').status_code,401);self.client.force_authenticate(self.user);self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book.id,'rating':5}).status_code,400);self.order(status=Order.STATUS_COMPLETED);r=self.client.post(self.url+'reviews/',{'book_id':self.book.id,'rating':5,'comment':'  好书  '},format='json');self.assertEqual(r.status_code,200);self.assertEqual(r.data['data']['book_detail']['id'],self.book.id);self.assertEqual(r.data['data']['comment'],'好书');self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book.id,'rating':4},format='json').status_code,400);self.book.refresh_from_db();self.assertEqual(self.book.rating,5)
    def test_review_statuses_and_isolation(self):
        for status in [Order.STATUS_PENDING,Order.STATUS_SUBMITTED,Order.STATUS_SHIPPED,Order.STATUS_CANCELLED]:
            self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book2.id,'rating':4},format='json').status_code,400) if status==Order.STATUS_PENDING else None
            self.order(status=status,book=self.book2); self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book2.id,'rating':4},format='json').status_code,400)
        self.order(user=self.other,book=self.off);self.assertEqual(self.client.get(self.url+'reviews/?book_id=999999').status_code,404);self.assertEqual(self.client.get(self.url+'reviews/?book_id=bad').status_code,400)
    def test_review_completed_different_users(self):
        self.order();self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book.id,'rating':4},format='json').status_code,200);self.client.force_authenticate(self.other);self.order(user=self.other);self.assertEqual(self.client.post(self.url+'reviews/',{'book_id':self.book.id,'rating':3},format='json').status_code,200);self.assertEqual(len(self.client.get(self.url+'reviews/me/').data['data']),1)
    def test_favorites_toggle_query_and_offsale(self):
        self.assertEqual(self.client.post(self.url+'favorites/toggle/',{'book_id':self.book.id}).data['data']['is_favorite'],True);self.assertEqual(self.client.post(self.url+'favorites/toggle/',{'book_id':self.book.id}).data['data']['action'],'removed');self.assertEqual(self.client.post(self.url+'favorites/toggle/',{'book_id':self.off.id}).status_code,400);self.assertEqual(self.client.get(self.url+'favorites/?book_id=bad').status_code,400);self.assertEqual(self.client.get(self.url+'favorites/?book_id=999').status_code,404)
    def test_favorite_isolation_and_downsale_cancel(self):
        Favorite.objects.create(user=self.user,book=self.off);self.assertEqual(self.client.post(self.url+'favorites/toggle/',{'book_id':self.off.id}).data['data']['is_favorite'],False);self.client.force_authenticate(self.other);self.assertEqual(self.client.get(self.url+'favorites/').data['data'],[])
    def test_history_dedupe_limit_isolation_and_clear(self):
        self.client.force_authenticate(None);self.assertEqual(self.client.get(self.url+'histories/').status_code,401);self.client.force_authenticate(self.user)
        for i in range(21):
            book=Book.objects.create(title=f'h{i}',author='a',isbn=f'his{i}',publisher='p');self.client.post(self.url+'histories/',{'book_id':book.id})
        self.assertEqual(BrowsingHistory.objects.filter(user=self.user).count(),20);first=BrowsingHistory.objects.filter(user=self.user).order_by('-created_at','-id').first();self.client.post(self.url+'histories/',{'book_id':first.book_id});self.assertEqual(BrowsingHistory.objects.filter(user=self.user,book_id=first.book_id).count(),1);self.assertEqual(self.client.delete(self.url+'histories/').data['data']['deleted_count'],20);self.client.force_authenticate(self.other);self.assertEqual(BrowsingHistory.objects.filter(user=self.other).count(),0)
    def test_offsale_history_requires_digital_purchase(self):
        self.assertEqual(self.client.post(self.url+'histories/',{'book_id':self.off.id}).status_code,400);self.order(book=self.off);DigitalBookPurchase.objects.create(user=self.user,book=self.off,order=Order.objects.latest('id'));self.assertEqual(self.client.post(self.url+'histories/',{'book_id':self.off.id}).status_code,200);row=self.client.get(self.url+'histories/').data['data'][0];self.assertIn('book_detail',row);self.assertFalse(row['book_is_on_sale'])
