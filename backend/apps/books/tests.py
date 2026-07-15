from datetime import timedelta

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.conf import settings
import os
from rest_framework.test import APIClient

from .models import Book, BookVersion, Category


class BookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='测试分类')

    def create_book(self, **kwargs):
        defaults = {
            'title': '测试书',
            'author': '测试作者',
            'isbn': 'isbn-test',
            'publisher': '测试出版社',
            'category': self.category,
            'is_on_sale': True,
            'on_shelf_date': timezone.now().date(),
        }
        defaults.update(kwargs)
        return Book.objects.create(**defaults)

    def create_version(self, book, version_type, sale_price, stock, is_on_sale=True):
        return BookVersion.objects.create(
            book=book,
            version_type=version_type,
            price=sale_price + Decimal('1.00'),
            sale_price=sale_price,
            stock=stock,
            is_on_sale=is_on_sale,
        )

    def test_page_size_query_returns_requested_count(self):
        for index in range(4):
            self.create_book(title=f'book-{index}', isbn=f'isbn-{index}')

        response = self.client.get('/api/books/', {'page_size': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 3)

    def test_list_includes_sale_price_and_stock(self):
        book = self.create_book(title='price-book', isbn='isbn-price')
        self.create_version(book, 'physical', Decimal('20.00'), 5)

        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()['results'][0]
        self.assertEqual(payload['sale_price'], '20.00')
        self.assertEqual(payload['stock'], 5)

    def test_detail_contains_versions(self):
        book = self.create_book(title='detail-book', isbn='isbn-detail')
        self.create_version(book, 'digital', Decimal('10.00'), 99)

        response = self.client.get(f'/api/books/{book.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('versions', response.json()['data'])

    def test_ordering_sale_price_works(self):
        first = self.create_book(title='first', isbn='isbn-first')
        second = self.create_book(title='second', isbn='isbn-second')
        self.create_version(first, 'physical', Decimal('15.00'), 1)
        self.create_version(second, 'physical', Decimal('25.00'), 2)

        response = self.client.get('/api/books/', {'ordering': 'sale_price'})
        self.assertEqual(response.status_code, 200)
        prices = [item['sale_price'] for item in response.json()['results']]
        self.assertEqual(prices, ['15.00', '25.00'])

    def test_ordering_negative_sale_price_works(self):
        first = self.create_book(title='third', isbn='isbn-third')
        second = self.create_book(title='fourth', isbn='isbn-fourth')
        self.create_version(first, 'physical', Decimal('15.00'), 1)
        self.create_version(second, 'physical', Decimal('25.00'), 2)

        response = self.client.get('/api/books/', {'ordering': '-sale_price'})
        self.assertEqual(response.status_code, 200)
        prices = [item['sale_price'] for item in response.json()['results']]
        self.assertEqual(prices, ['25.00', '15.00'])

    def test_home_new_books_uses_recent_shelf_without_7_day_requirement(self):
        old_book = self.create_book(title='old-book', isbn='isbn-old', on_shelf_date=(timezone.now().date() - timedelta(days=30)))
        recent_book = self.create_book(title='recent-book', isbn='isbn-recent', on_shelf_date=(timezone.now().date() - timedelta(days=2)))
        self.create_version(old_book, 'physical', Decimal('12.00'), 3)
        self.create_version(recent_book, 'physical', Decimal('18.00'), 4)

        response = self.client.get('/api/books/home/')
        self.assertEqual(response.status_code, 200)
        new_books = response.json()['data']['new_books']
        self.assertTrue(any(item['title'] == 'recent-book' for item in new_books))
        self.assertTrue(any(item['title'] == 'old-book' for item in new_books))

    def test_home_ignores_list_query_params(self):
        self.create_book(title='recent-home', isbn='isbn-home-recent', on_shelf_date=(timezone.now().date() - timedelta(days=2)))
        self.create_book(title='older-home', isbn='isbn-home-older', on_shelf_date=(timezone.now().date() - timedelta(days=20)))

        response = self.client.get('/api/books/home/?is_new=true&ordering=sale_price')
        self.assertEqual(response.status_code, 200)
        new_books = response.json()['data']['new_books']
        self.assertTrue(any(item['title'] == 'recent-home' for item in new_books))
        self.assertTrue(any(item['title'] == 'older-home' for item in new_books))

    def test_is_new_filter_uses_last_7_days(self):
        recent = self.create_book(title='recent', isbn='isbn-recent-filter', on_shelf_date=(timezone.now().date() - timedelta(days=2)))
        old = self.create_book(title='old', isbn='isbn-old-filter', on_shelf_date=(timezone.now().date() - timedelta(days=10)))
        self.create_version(recent, 'physical', Decimal('9.00'), 1)
        self.create_version(old, 'physical', Decimal('8.00'), 2)

        response = self.client.get('/api/books/', {'is_new': 'true'})
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.json()['results']]
        self.assertEqual(titles, ['recent'])

    def test_falls_back_to_digital_when_no_physical_version(self):
        book = self.create_book(title='digital-only', isbn='isbn-digital')
        self.create_version(book, 'digital', Decimal('33.00'), 7)

        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()['results'][0]
        self.assertEqual(payload['sale_price'], '33.00')
        self.assertEqual(payload['stock'], 7)

    def test_unknown_ordering_falls_back_to_default_sort(self):
        first = self.create_book(title='zzz-book', isbn='isbn-zzz')
        second = self.create_book(title='aaa-book', isbn='isbn-aaa')
        self.create_version(first, 'physical', Decimal('20.00'), 1)
        self.create_version(second, 'physical', Decimal('10.00'), 1)

        response = self.client.get('/api/books/', {'ordering': 'unknown_field'})
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.json()['results']]
        self.assertEqual(titles, ['aaa-book', 'zzz-book'])

    def test_no_on_sale_versions_returns_null_prices(self):
        book = self.create_book(title='no-version-book', isbn='isbn-no-version')
        BookVersion.objects.create(
            book=book,
            version_type='physical',
            price=Decimal('15.00'),
            sale_price=Decimal('15.00'),
            stock=5,
            is_on_sale=False,
        )

        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()['results'][0]
        self.assertIsNone(payload['sale_price'])
        self.assertIsNone(payload['stock'])

    def test_price_min_filters_by_representative_sale_price(self):
        low = self.create_book(title='low-price', isbn='isbn-low-price')
        high = self.create_book(title='high-price', isbn='isbn-high-price')
        self.create_version(low, 'physical', Decimal('20.00'), 1)
        self.create_version(high, 'physical', Decimal('40.00'), 1)

        response = self.client.get('/api/books/', {'price_min': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.json()['results']], ['high-price'])

    def test_price_max_filters_by_representative_sale_price(self):
        low = self.create_book(title='low-max-price', isbn='isbn-low-max-price')
        high = self.create_book(title='high-max-price', isbn='isbn-high-max-price')
        self.create_version(low, 'physical', Decimal('20.00'), 1)
        self.create_version(high, 'physical', Decimal('40.00'), 1)

        response = self.client.get('/api/books/', {'price_max': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.json()['results']], ['low-max-price'])

    def test_price_range_filters_by_representative_sale_price(self):
        low = self.create_book(title='range-low', isbn='isbn-range-low')
        middle = self.create_book(title='range-middle', isbn='isbn-range-middle')
        high = self.create_book(title='range-high', isbn='isbn-range-high')
        self.create_version(low, 'physical', Decimal('20.00'), 1)
        self.create_version(middle, 'physical', Decimal('35.00'), 1)
        self.create_version(high, 'physical', Decimal('50.00'), 1)

        response = self.client.get('/api/books/', {'price_min': '30', 'price_max': '40'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.json()['results']], ['range-middle'])

    def test_invalid_price_filter_returns_400(self):
        response = self.client.get('/api/books/', {'price_min': 'NaN'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('price_min', response.json())

    def test_price_filter_excludes_books_without_on_sale_versions(self):
        available = self.create_book(title='priced-book', isbn='isbn-priced-book')
        missing = self.create_book(title='no-priced-version', isbn='isbn-no-priced-version')
        self.create_version(available, 'physical', Decimal('20.00'), 1)
        self.create_version(missing, 'physical', Decimal('10.00'), 1, is_on_sale=False)

        response = self.client.get('/api/books/', {'price_min': '0'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.json()['results']], ['priced-book'])

class ReadingContractTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        from apps.orders.models import DigitalBookPurchase
        from tempfile import TemporaryDirectory
        temp_parent = os.path.join(str(settings.BASE_DIR.parent), '.media_test_tmp')
        os.makedirs(temp_parent, exist_ok=True)
        self.tmp = TemporaryDirectory(dir=temp_parent); self.addCleanup(self.tmp.cleanup)
        self.client = APIClient(); self.user = get_user_model().objects.create_user(username='reader', phone='13900000111', password='knownpass')
        self.book = Book.objects.create(title='阅读测试', author='作者', isbn='isbn-reading', publisher='出版社', is_on_sale=True, content_file_path='test.txt')
        self.path = __import__('pathlib').Path(self.tmp.name); (self.path / 'test.txt').write_text('第一章 测试内容。这是一段仅用于自动化测试的短文本。', encoding='utf-8')
        self.override = self.settings(MEDIA_ROOT=self.tmp.name); self.override.enable(); self.addCleanup(self.override.disable)
        self.purchase_model = DigitalBookPurchase; self.client.force_authenticate(self.user)
    def test_preview_and_read_permissions(self):
        response = self.client.get(f'/api/books/{self.book.id}/preview/'); self.assertEqual(response.status_code, 200); data=response.data['data']; self.assertEqual(data['total_length'], len(data['content']) if data['is_complete'] else data['total_length']); self.assertEqual(data['preview_length'], len(data['content']))
        self.assertEqual(self.client.get(f'/api/books/{self.book.id}/read/').status_code, 403)
        from apps.orders.models import Order
        order = Order.objects.create(order_no='READTEST01', user=self.user, receiver='x', receiver_phone='13900000000', receiver_address='x', total_amount=0, pay_amount=0)
        self.purchase_model.objects.create(user=self.user, book=self.book, order=order)
        response = self.client.get(f'/api/books/{self.book.id}/read/')
        self.assertEqual(response.status_code, 200); self.assertEqual(response.data['data']['total_length'], len(response.data['data']['content']))
        self.book.is_on_sale = False; self.book.save()
        self.assertEqual(self.client.get(f'/api/books/{self.book.id}/read/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/books/{self.book.id}/').status_code, 200)
