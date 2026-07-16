from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.books.models import Book, BookVersion
from .models import Cart

User = get_user_model()

class CartContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='cartuser', phone='13800000001', password='knownpass')
        self.other = User.objects.create_user(username='otheruser', phone='13800000002', password='knownpass')
        self.book = Book.objects.create(title='测试书', author='作者', isbn='9780000000001', publisher='出版社', is_on_sale=True)
        self.digital = BookVersion.objects.create(book=self.book, version_type='digital', price=Decimal('29.90'), sale_price=Decimal('19.90'), stock=0, is_on_sale=True)
        self.physical = BookVersion.objects.create(book=self.book, version_type='physical', price=Decimal('59.90'), sale_price=Decimal('49.90'), stock=3, is_on_sale=True)
        self.client.force_authenticate(self.user)
        self.url = '/api/cart/'

    def add(self, version, quantity=1):
        return self.client.post(self.url, {'book_id': self.book.pk, 'version_type': version, 'quantity': quantity}, format='json')

    def test_unauthenticated_and_empty(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.url).data['items'], [])

    def test_add_versions_and_accumulate(self):
        self.assertEqual(self.add('physical', 1).status_code, 200)
        self.assertEqual(self.add('digital', 2).status_code, 200)
        self.assertEqual(self.add('physical', 1).status_code, 200)
        self.assertEqual(Cart.objects.get(user=self.user, version_type='physical').quantity, 2)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 2)
        response = self.add('physical', 2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Cart.objects.get(user=self.user, version_type='physical').quantity, 2)

    def test_response_and_version_prices(self):
        self.add('physical', 2); self.add('digital', 1)
        data = self.client.get(self.url).data
        rows = {row['version_type']: row for row in data['items']}
        self.assertEqual(rows['physical']['version_label'], self.physical.get_version_type_display())
        self.assertEqual(rows['physical']['unit_price'], '49.90'); self.assertEqual(rows['physical']['subtotal'], '99.80')
        self.assertEqual(rows['physical']['stock'], 3); self.assertTrue(rows['physical']['is_valid']); self.assertEqual(rows['physical']['invalid_reason'], '')
        self.assertEqual(rows['digital']['unit_price'], '19.90'); self.assertEqual(str(data['selected_total']), '119.70')

    def test_update_uses_version_stock_and_digital_unlimited(self):
        physical = self.add('physical').data['data']['id']; digital = self.add('digital').data['data']['id']
        self.assertEqual(self.client.put(f'{self.url}{physical}/', {'quantity': 3}, format='json').status_code, 200)
        self.assertEqual(self.client.put(f'{self.url}{physical}/', {'quantity': 4}, format='json').status_code, 400)
        self.physical.stock = 0; self.physical.save()
        self.assertEqual(self.client.put(f'{self.url}{digital}/', {'quantity': 10}, format='json').status_code, 200)

    def test_invalid_rules_and_clear(self):
        p = self.add('physical').data['data']['id']; d = self.add('digital').data['data']['id']
        self.physical.stock = 0; self.physical.save()
        data = self.client.get(self.url).data
        reasons = {x['id']: x for x in data['items']}
        self.assertFalse(reasons[p]['is_valid']); self.assertEqual(reasons[p]['invalid_reason'], '纸质版库存不足')
        self.assertTrue(reasons[d]['is_valid'])
        self.physical.is_on_sale = False; self.physical.save()
        self.assertEqual(self.client.delete(f'{self.url}clear-invalid/').status_code, 200)
        self.assertFalse(Cart.objects.filter(pk=p).exists()); self.assertTrue(Cart.objects.filter(pk=d).exists())

    def test_missing_or_offsale_version_is_invalid(self):
        item = Cart.objects.create(user=self.user, book=self.book, version_type='digital')
        self.digital.is_on_sale = False; self.digital.save()
        row = next(x for x in self.client.get(self.url).data['items'] if x['id'] == item.id)
        self.assertEqual(row['invalid_reason'], '该版本已下架')

    def test_user_isolation_for_item_and_batch_operations(self):
        item = self.add('physical').data['data']['id']
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.put(f'{self.url}{item}/', {'quantity': 2}, format='json').status_code, 400)
        self.assertEqual(self.client.delete(f'{self.url}{item}/').status_code, 200)
        self.assertTrue(Cart.objects.filter(pk=item).exists())
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f'{self.url}batch/', {'item_ids':[item], 'is_selected':False}, format='json').status_code, 200)
        self.assertFalse(Cart.objects.get(pk=item).is_selected)
        self.client.delete(f'{self.url}batch/', {'item_ids':[item]}, format='json')
        self.assertFalse(Cart.objects.filter(pk=item).exists())
