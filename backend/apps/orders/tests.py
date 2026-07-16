from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.books.models import Book, BookVersion
from apps.cart.models import Cart
from .models import Order, OrderItem, DigitalBookPurchase

User = get_user_model()

class OrderContractTests(TestCase):
    def setUp(self):
        self.client = APIClient(); self.user = User.objects.create_user(username='orderuser', phone='13800000101', password='knownpass'); self.other = User.objects.create_user(username='otherorder', phone='13800000102', password='knownpass')
        self.book = Book.objects.create(title='订单测试书', author='作者', isbn='9780000000021', publisher='出版社', is_on_sale=True)
        self.digital = BookVersion.objects.create(book=self.book, version_type='digital', price=Decimal('20.00'), sale_price=Decimal('12.50'), stock=0, is_on_sale=True)
        self.physical = BookVersion.objects.create(book=self.book, version_type='physical', price=Decimal('40.00'), sale_price=Decimal('35.00'), stock=5, is_on_sale=True)
        self.client.force_authenticate(self.user); self.url = '/api/orders/'
    def cart(self, version, quantity=1, selected=True, user=None): return Cart.objects.create(user=user or self.user, book=self.book, version_type=version, quantity=quantity, is_selected=selected)
    def create(self, ids): return self.client.post(self.url, {'address':' 北京 地址 ', 'receiver':' 张三 ', 'phone':'13900000001', 'cart_item_ids':ids, 'remark':''}, format='json')

    def test_auth_empty_and_isolation(self):
        self.client.force_authenticate(None); self.assertEqual(self.client.get(self.url).status_code, 401); self.client.force_authenticate(self.user); self.assertEqual(self.client.get(self.url).data['data'], [])
        other = Order.objects.create(order_no='OTHER0001', user=self.other, receiver='x', receiver_phone='13900000002', receiver_address='x', total_amount=1, pay_amount=1)
        self.assertEqual(self.client.get(f'{self.url}{other.id}/').status_code, 404)

    def test_create_mixed_snapshot_amount_inventory_and_cart_cleanup(self):
        p = self.cart('physical', 2); d = self.cart('digital', 1); other_book = Book.objects.create(title='未提交书', author='作者', isbn='9780000000022', publisher='出版社', is_on_sale=True); untouched = Cart.objects.create(user=self.user, book=other_book, version_type='digital', quantity=1, is_selected=False)
        response = self.create([p.id, d.id]); self.assertEqual(response.status_code, 200); order = Order.objects.get(); self.assertEqual(order.total_amount, Decimal('82.50')); self.assertEqual(order.pay_amount, Decimal('82.50')); self.assertEqual(self.physical.refresh_from_db() or self.physical.stock, 3)
        self.assertTrue(Cart.objects.filter(pk=untouched.pk).exists()); self.assertFalse(Cart.objects.filter(pk=p.pk).exists()); self.assertFalse(Cart.objects.filter(pk=d.pk).exists())
        item = order.items.get(version_type='digital'); self.assertEqual(item.version_type, 'digital'); self.assertEqual(item.sale_price, Decimal('12.50')); self.assertEqual(item.get_version_type_display(), '电子版')
        self.book.title='已修改'; self.book.save(); self.assertEqual(order.items.first().book_title, '订单测试书')

    def test_strict_cart_validation_is_atomic(self):
        p = self.cart('physical', 2); other = self.cart('digital', user=self.other); unselected = self.cart('digital', selected=False)
        for ids in ([p.id, 999999], [p.id, other.id], [p.id, unselected.id], [p.id, p.id]):
            response = self.create(ids); self.assertEqual(response.status_code, 400); self.assertEqual(Order.objects.count(), 0); self.assertTrue(Cart.objects.filter(pk=p.pk).exists()); self.physical.refresh_from_db(); self.assertEqual(self.physical.stock, 5)

    def test_invalid_book_version_and_stock(self):
        p = self.cart('physical', 6); self.assertEqual(self.create([p.id]).status_code, 400); self.assertEqual(Order.objects.count(), 0)
        self.physical.stock=5; self.physical.is_on_sale=False; self.physical.save(); self.assertEqual(self.create([p.id]).status_code, 400)
        self.physical.is_on_sale=True; self.physical.save(); self.book.is_on_sale=False; self.book.save(); self.assertEqual(self.create([p.id]).status_code, 400)

    def test_pay_digital_and_mixed_create_permissions_idempotently(self):
        d = self.cart('digital'); order = Order.objects.get(pk=self.create([d.id]).data['data']['id']); self.client.put(f'{self.url}{order.id}/', {'action':'pay'}, format='json'); order.refresh_from_db(); self.assertEqual(order.status, Order.STATUS_COMPLETED); self.assertTrue(DigitalBookPurchase.objects.filter(user=self.user, book=self.book).exists()); self.assertEqual(self.client.put(f'{self.url}{order.id}/', {'action':'pay'}, format='json').status_code, 400)
        self.assertEqual(DigitalBookPurchase.objects.count(), 1)

    def test_cancel_only_restores_physical_and_confirm_status(self):
        p = self.cart('physical'); order = Order.objects.get(pk=self.create([p.id]).data['data']['id']); self.client.put(f'{self.url}{order.id}/', {'action':'cancel'}, format='json'); self.physical.refresh_from_db(); self.assertEqual(self.physical.stock, 5); order.refresh_from_db(); self.assertEqual(order.status, Order.STATUS_CANCELLED); self.assertEqual(self.client.put(f'{self.url}{order.id}/', {'action':'cancel'}, format='json').status_code, 400)
        self.assertEqual(self.client.get(f'{self.url}?status=bad').status_code, 400); self.assertEqual(self.client.get(f'{self.url}?status=9').status_code, 400); self.assertEqual(self.client.get(f'{self.url}?status=5').status_code, 200)

    def test_bookshelf_and_mixed_digital_permission(self):
        p=self.cart('physical'); d=self.cart('digital'); order=Order.objects.get(pk=self.create([p.id,d.id]).data['data']['id']); self.client.put(f'{self.url}{order.id}/', {'action':'pay'}, format='json'); self.assertEqual(order.items.count(), 2); self.assertEqual(self.client.get('/api/orders/bookshelf/').data['data'][0]['title'], '订单测试书')
