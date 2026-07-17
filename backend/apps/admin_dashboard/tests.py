from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderItem
from apps.books.models import Book, BookVersion, Category


User = get_user_model()


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username='staffadmin', phone='13920000001', password='knownpass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='superadmin', phone='13920000002', password='knownpass')
        self.user = User.objects.create_user(username='normaluser', phone='13920000003', password='knownpass')
        self.other = User.objects.create_user(username='otheruser', phone='13920000004', password='knownpass')
        self.orders = '/api/admin/orders/'; self.users = '/api/admin/users/'
        self.books = '/api/admin/books/'; self.categories = '/api/admin/categories/'
        self.summary = '/api/admin/dashboard/summary/'
        self.category = Category.objects.create(name='测试分类', sort=2)
        self.off_book = Book.objects.create(title='下架书', author='作者甲', isbn='9780000000001', publisher='测试社', category=self.category, is_on_sale=False)
        self.on_book = Book.objects.create(title='上架书', author='作者乙', isbn='9780000000002', publisher='测试社', category=self.category)
        BookVersion.objects.create(book=self.off_book, version_type='digital', price=Decimal('20'), sale_price=Decimal('10'), stock=99999)
        BookVersion.objects.create(book=self.on_book, version_type='physical', price=Decimal('30'), sale_price=Decimal('20'), stock=5)

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
        missing_no = self.client.put(f'{self.orders}{physical.id}/action/', {'action':'ship','express_no':'','express_company':'顺丰'}, format='json')
        self.assertEqual(missing_no.status_code, 400); self.assertIn('快递单号不能为空', str(missing_no.data))
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

    def test_admin_books_permissions_filters_and_categories(self):
        self.assertEqual(self.client.get(self.books).status_code, 401)
        self.client.force_authenticate(self.user); self.assertEqual(self.client.get(self.books).status_code, 403); self.assertEqual(self.client.get(self.categories).status_code, 403)
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.books, {'keyword':'作者甲', 'page':1, 'page_size':1})
        self.assertEqual(response.status_code, 200); self.assertEqual(response.data['data']['total'], 1); self.assertFalse(response.data['data']['items'][0]['is_on_sale'])
        self.assertEqual(self.client.get(self.books, {'is_on_sale':'no'}).status_code, 400)
        self.assertEqual(self.client.get(self.books, {'page':0}).status_code, 400)
        self.assertEqual(self.client.get(self.books, {'page_size':101}).status_code, 400)
        categories = self.client.get(self.categories); self.assertEqual(categories.status_code, 200); self.assertIn('parent_name', categories.data['data'][0])
        self.assertEqual(categories.data['data'][0]['book_count'], 2); self.assertIn('description', categories.data['data'][0]); self.assertIn('is_active', categories.data['data'][0])
        self.client.force_authenticate(self.superuser); self.assertEqual(self.client.get(self.books).status_code, 200)

    def test_admin_category_crud_hierarchy_and_delete_rules(self):
        payload = {'name':' 文学 ', 'parent':None, 'sort':3, 'description':' 小说与散文 ', 'is_active':False}
        self.assertEqual(self.client.post(self.categories, payload, format='json').status_code, 401)
        self.client.force_authenticate(self.user); self.assertEqual(self.client.post(self.categories, payload, format='json').status_code, 403)
        self.client.force_authenticate(self.staff)
        created = self.client.post(self.categories, payload, format='json')
        self.assertEqual(created.status_code, 201); category_id = created.data['data']['id']
        self.assertEqual(created.data['data']['name'], '文学'); self.assertEqual(created.data['data']['description'], '小说与散文'); self.assertFalse(created.data['data']['is_active'])
        self.assertEqual(self.client.post(self.categories, {**payload, 'name':'文学'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.categories, {**payload, 'name':'错误排序', 'sort':-1}, format='json').status_code, 400)
        child = self.client.post(self.categories, {'name':'中国文学', 'parent':category_id}, format='json')
        self.assertEqual(child.status_code, 201); child_id = child.data['data']['id']
        updated = self.client.put(f'{self.categories}{child_id}/', {'name':'中国现当代文学', 'sort':8}, format='json')
        self.assertEqual(updated.status_code, 200); self.assertEqual(updated.data['data']['parent'], category_id)
        self.assertEqual(self.client.put(f'{self.categories}{category_id}/', {'parent':child_id}, format='json').status_code, 400)
        self.assertEqual(self.client.delete(f'{self.categories}{category_id}/').status_code, 400)
        self.on_book.category_id = child_id; self.on_book.save(update_fields=['category'])
        deleted = self.client.delete(f'{self.categories}{child_id}/')
        self.assertEqual(deleted.status_code, 200); self.assertEqual(deleted.data['data']['affected_books'], 1)
        self.on_book.refresh_from_db(); self.assertIsNone(self.on_book.category_id)
        self.assertEqual(self.client.delete(f'{self.categories}{category_id}/').status_code, 200)

    def test_admin_category_add_remove_books_and_validation(self):
        target = Category.objects.create(name='目标分类')
        endpoint = f'{self.categories}{target.id}/books/'
        self.client.force_authenticate(self.staff)
        added = self.client.put(endpoint, {'action':'add', 'book_ids':[self.off_book.id, self.on_book.id]}, format='json')
        self.assertEqual(added.status_code, 200); self.assertEqual(added.data['data']['changed'], 2); self.assertEqual(added.data['data']['category']['book_count'], 2)
        listed = self.client.get(endpoint, {'keyword':'作者甲'})
        self.assertEqual(listed.status_code, 200); self.assertEqual(listed.data['data']['total'], 1); self.assertEqual(listed.data['data']['items'][0]['id'], self.off_book.id)
        removed = self.client.put(endpoint, {'action':'remove', 'book_ids':[self.off_book.id]}, format='json')
        self.assertEqual(removed.status_code, 200); self.assertEqual(removed.data['data']['changed'], 1)
        self.off_book.refresh_from_db(); self.assertIsNone(self.off_book.category_id)
        self.assertEqual(self.client.put(endpoint, {'action':'add', 'book_ids':[999999]}, format='json').status_code, 400)
        self.assertEqual(self.client.put(endpoint, {'action':'add', 'book_ids':[self.on_book.id, self.on_book.id]}, format='json').status_code, 400)

    def test_admin_book_create_update_sale_and_validation(self):
        self.client.force_authenticate(self.staff)
        payload = {'title':' 新书 ', 'author':' 新作者 ', 'isbn':'9780000000003', 'publisher':' 新社 ', 'is_on_sale':True, 'category':self.category.id, 'versions':[{'version_type':'digital','price':'20.00','sale_price':'10.00','stock':0,'is_on_sale':True}, {'version_type':'physical','price':'30.00','sale_price':'20.00','stock':3,'is_on_sale':True}]}
        created = self.client.post(self.books, payload, format='json'); self.assertEqual(created.status_code, 201); book_id = created.data['data']['id']; self.assertEqual(len(created.data['data']['versions']), 2)
        self.assertEqual(self.client.post(self.books, {**payload, 'isbn':'9780000000004', 'versions':[]}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.books, {**payload, 'isbn':'9780000000005', 'versions':[{'version_type':'digital','price':'1','sale_price':'2','stock':0,'is_on_sale':True}]}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.books, {**payload, 'isbn':'9780000000006', 'sales_count':99}, format='json').status_code, 400)
        updated = self.client.put(f'{self.books}{book_id}/', {'title':'更新书名','versions':[{'version_type':'physical','price':'30','sale_price':'18','stock':9,'is_on_sale':False}]}, format='json'); self.assertEqual(updated.status_code, 200); self.assertEqual(len(updated.data['data']['versions']), 2)
        sale = self.client.put(f'{self.books}{book_id}/sale/', {'is_on_sale':False}, format='json'); self.assertEqual(sale.status_code, 200); self.assertFalse(sale.data['data']['is_on_sale'])
        self.assertEqual(self.client.put(f'{self.books}{book_id}/sale/', {'is_on_sale':True,'title':'x'}, format='json').status_code, 400)
        self.assertEqual(self.client.delete(f'{self.books}{book_id}/').status_code, 405)

    def test_admin_book_validation_messages_are_utf8(self):
        self.client.force_authenticate(self.staff)
        base = {'title':'提示测试书','author':'提示作者','isbn':'9780000000099','publisher':'提示社','is_on_sale':True,'versions':[{'version_type':'digital','price':'20','sale_price':'10','stock':0,'is_on_sale':True}]}
        cases = [
            self.client.post(self.books, {**base, 'isbn':self.on_book.isbn}, format='json'),
            self.client.post(self.books, {**base, 'isbn':'9780000000098', 'cover_image':'https://example.com/../unsafe.png'}, format='json'),
            self.client.post(self.books, {**base, 'isbn':'9780000000097', 'content_file_path':'../secret.txt'}, format='json'),
            self.client.post(self.books, {**base, 'isbn':'9780000000096', 'versions':[base['versions'][0], base['versions'][0]]}, format='json'),
            self.client.post(self.books, {**base, 'isbn':'9780000000095', 'versions':[{'version_type':'digital','price':'10','sale_price':'11','stock':0,'is_on_sale':True}]}, format='json'),
        ]
        expected = ['ISBN 已存在', '封面路径不安全', '正文文件不可用', '版本类型不能重复', '销售价不能高于定价']
        for response, message in zip(cases, expected):
            self.assertEqual(response.status_code, 400); text = str(response.data); self.assertIn(message, text)
            for fragment in ('涓', '鍙', '璇', '閿'): self.assertNotIn(fragment, text)

    def test_dashboard_summary_permissions_empty_and_read_only_methods(self):
        self.assertEqual(self.client.get(self.summary).status_code, 401)
        self.client.force_authenticate(self.user); self.assertEqual(self.client.get(self.summary).status_code, 403)
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.summary); self.assertEqual(response.status_code, 200)
        data = response.data['data']; self.assertEqual(data['sales']['paid_amount'], '0.00'); self.assertEqual(set(data), {'users', 'books', 'orders', 'sales', 'low_stock', 'recent_orders'})
        for method in ('post', 'put', 'patch', 'delete'): self.assertEqual(getattr(self.client, method)(self.summary, {}, format='json').status_code, 405)
        self.client.force_authenticate(self.superuser); self.assertEqual(self.client.get(self.summary).status_code, 200)

    def test_dashboard_summary_aggregates_paid_quantities_stock_and_recent_orders(self):
        self.user.is_active = False; self.user.save(); User.objects.create_user(username='stafftwo', phone='13920000005', password='knownpass', is_staff=True)
        low = BookVersion.objects.create(book=self.on_book, version_type='digital', price=Decimal('5'), sale_price=Decimal('5'), stock=99999)
        extra = Book.objects.create(title='低库存书', author='作者', isbn='9780000000100', publisher='测试社', is_on_sale=True)
        low_physical = BookVersion.objects.create(book=extra, version_type='physical', price=Decimal('8'), sale_price=Decimal('6'), stock=2, is_on_sale=True)
        BookVersion.objects.create(book=extra, version_type='digital', price=Decimal('8'), sale_price=Decimal('6'), stock=1, is_on_sale=True)
        stopped_book = Book.objects.create(title='停售库存书', author='作者', isbn='9780000000101', publisher='测试社', is_on_sale=True)
        stopped = BookVersion.objects.create(book=stopped_book, version_type='physical', price=Decimal('8'), sale_price=Decimal('6'), stock=1, is_on_sale=False)
        paid = self.order(status=Order.STATUS_SUBMITTED, kinds=('physical', 'digital')); paid.pay_amount = Decimal('12.50'); paid.save(update_fields=['pay_amount'])
        shipped = self.order(status=Order.STATUS_SHIPPED, kinds=('physical',)); shipped.pay_amount = Decimal('7.00'); shipped.save(update_fields=['pay_amount'])
        self.order(status=Order.STATUS_COMPLETED, kinds=('digital',))
        self.order(status=Order.STATUS_PENDING); self.order(status=Order.STATUS_CANCELLED)
        self.client.force_authenticate(self.staff); response = self.client.get(self.summary); self.assertEqual(response.status_code, 200); data = response.data['data']
        self.assertEqual(data['users']['disabled'], 1); self.assertGreaterEqual(data['users']['staff'], 2)
        self.assertEqual(data['books']['off_sale'], 1); self.assertGreaterEqual(data['books']['digital_versions'], 3); self.assertGreaterEqual(data['books']['physical_versions'], 3)
        self.assertEqual(data['orders']['pending'], 1); self.assertEqual(data['orders']['cancelled'], 1); self.assertEqual(data['sales']['paid_order_count'], 3); self.assertEqual(data['sales']['paid_amount'], '29.50'); self.assertEqual(data['sales']['physical_quantity'], 2); self.assertEqual(data['sales']['digital_quantity'], 2)
        self.assertEqual(data['low_stock'][0]['version_id'], low_physical.id); self.assertNotIn(stopped.id, [item['version_id'] for item in data['low_stock']]); self.assertNotIn(low.id, [item['version_id'] for item in data['low_stock']])
        self.assertLessEqual(len(data['recent_orders']), 5); self.assertNotIn('receiver_phone', data['recent_orders'][0]); self.assertNotIn('receiver_address', data['recent_orders'][0])
