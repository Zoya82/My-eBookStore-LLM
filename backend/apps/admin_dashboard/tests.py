from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderItem


User = get_user_model()


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username='staffadmin', phone='13920000001', password='knownpass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='superadmin', phone='13920000002', password='knownpass')
        self.user = User.objects.create_user(username='normaluser', phone='13920000003', password='knownpass')
        self.other = User.objects.create_user(username='otheruser', phone='13920000004', password='knownpass')
        self.orders = '/api/admin/orders/'; self.users = '/api/admin/users/'

    def order(self, user=None, status=Order.STATUS_SUBMITTED, kinds=('physical',)):
        order = Order.objects.create(order_no=f'ADM{Order.objects.count()+1:07d}', user=user or self.user, receiver='张三', receiver_phone='13800138000', receiver_address='北京海淀', total_amount=Decimal('10'), pay_amount=Decimal('10'), status=status)
        for index, kind in enumerate(kinds): OrderItem.objects.create(order=order, book_id=100+index, book_title='测试书', book_cover='', book_author='作者', sale_price=Decimal('10'), quantity=1, subtotal=Decimal('10'), version_type=kind)
        return order

    def test_permissions_staff_and_superuser(self):
        self.assertEqual(self.client.get(self.orders).status_code, 401)
        self.client.force_authenticate(self.user); self.assertEqual(self.client.get(self.orders).status_code, 403)
        self.client.force_authenticate(self.staff); self.assertEqual(self.client.get(self.orders).status_code, 200)
        self.client.force_authenticate(self.superuser); self.assertEqual(self.client.get(self.orders).status_code, 200)

    def test_orders_filters_and_detail(self):
        first = self.order(); second = self.order(user=self.other, status=Order.STATUS_PENDING)
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.orders, {'status': Order.STATUS_SUBMITTED, 'order_no': ' ADM', 'receiver': ' 张三 '})
        self.assertEqual(response.status_code, 200); self.assertEqual(len(response.data['data']), 1); self.assertEqual(response.data['data'][0]['id'], first.id)
        self.assertEqual(self.client.get(self.orders, {'status': 'bad'}).status_code, 400)
        self.assertEqual(self.client.get(f'{self.orders}{second.id}/').status_code, 200)
        self.assertEqual(self.client.get(f'{self.orders}999999/').status_code, 404)

    def test_shipping_rules(self):
        physical = self.order(); mixed = self.order(kinds=('digital', 'physical')); digital = self.order(kinds=('digital',)); pending = self.order(status=Order.STATUS_PENDING)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.put(f'{self.orders}{physical.id}/action/', {'action':'ship','express_no':'','express_company':'顺丰'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(f'{self.orders}{digital.id}/action/', {'action':'ship','express_no':'SF1','express_company':'顺丰'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(f'{self.orders}{pending.id}/action/', {'action':'ship','express_no':'SF2','express_company':'顺丰'}, format='json').status_code, 400)
        response = self.client.put(f'{self.orders}{mixed.id}/action/', {'action':'ship','express_no':' SF3 ','express_company':' 顺丰 '}, format='json')
        self.assertEqual(response.status_code, 200); mixed.refresh_from_db(); self.assertEqual(mixed.status, Order.STATUS_SHIPPED); self.assertEqual(mixed.express_no, 'SF3')
        self.assertEqual(self.client.put(f'{self.orders}{mixed.id}/action/', {'action':'ship','express_no':'SF3','express_company':'顺丰'}, format='json').status_code, 400)

    def test_cancel_uses_service_rules(self):
        cancellable = self.order(); completed = self.order(status=Order.STATUS_COMPLETED)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.put(f'{self.orders}{cancellable.id}/action/', {'action':'cancel'}, format='json').status_code, 200); cancellable.refresh_from_db(); self.assertEqual(cancellable.status, Order.STATUS_CANCELLED)
        self.assertEqual(self.client.put(f'{self.orders}{completed.id}/action/', {'action':'cancel'}, format='json').status_code, 400)

    def test_user_list_pagination_and_toggle_guards(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.users, {'keyword':' normal ', 'page':1, 'page_size':1})
        self.assertEqual(response.status_code, 200); self.assertEqual(response.data['data']['total'], 1)
        self.assertEqual(self.client.get(self.users, {'page':0}).status_code, 400); self.assertEqual(self.client.get(self.users, {'page_size':101}).status_code, 400)
        self.assertEqual(self.client.put(f'{self.users}{self.user.id}/toggle/', {'is_active':False}, format='json').status_code, 200); self.user.refresh_from_db(); self.assertFalse(self.user.is_active)
        self.assertEqual(self.client.put(f'{self.users}{self.staff.id}/toggle/', {'is_active':False}, format='json').status_code, 400)
        self.assertEqual(self.client.put(f'{self.users}{self.superuser.id}/toggle/', {'is_active':False}, format='json').status_code, 400)
        self.assertEqual(self.client.put(f'{self.users}{self.other.id}/toggle/', {'is_active':True,'is_staff':True}, format='json').status_code, 400)
