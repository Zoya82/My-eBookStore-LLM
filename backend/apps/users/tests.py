from datetime import datetime, timedelta
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

class AddressContractTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='addressuser', phone='13910000001', password='knownpass')
        self.other = User.objects.create_user(username='addressother', phone='13910000002', password='knownpass')
        self.url = '/api/users/addresses/'
    def data(self, **extra):
        value = {'receiver':' 张三 ','phone':'13800138000','province':' 北京 ','city':' 北京市 ','district':' 海淀区 ','detail':' 中关村  ','is_default':False}; value.update(extra); return value
    def test_address_crud_default_validation_and_isolation(self):
        self.assertEqual(self.client.get(self.url).status_code, 401); self.client.force_authenticate(self.user)
        first = self.client.post(self.url, self.data(), format='json'); self.assertEqual(first.status_code, 200); self.assertTrue(first.data['data']['is_default'])
        second = self.client.post(self.url, self.data(phone='13800138001'), format='json'); self.assertEqual(second.status_code, 200)
        self.assertEqual(self.client.put(self.url + str(second.data['data']['id']) + '/', self.data(is_default=True), format='json').status_code, 200)
        self.assertFalse(self.client.get(self.url).data['data'][1]['is_default'])
        self.assertEqual(self.client.put(self.url + str(first.data['data']['id']) + '/', self.data(receiver='李四'), format='json').status_code, 200)
        self.assertEqual(self.client.delete(self.url + str(first.data['data']['id']) + '/').status_code, 200)
        self.assertEqual(self.client.post(self.url, self.data(phone='123'), format='json').status_code, 400)
        self.client.force_authenticate(self.other); self.assertEqual(self.client.put(self.url + str(second.data['data']['id']) + '/', self.data(), format='json').status_code, 404); self.assertEqual(self.client.delete(self.url + str(second.data['data']['id']) + '/').status_code, 404)

class UserAuthTests(APITestCase):
    def setUp(self):
        self.register = '/api/users/register/'
        self.login = '/api/users/login/'
        self.profile = '/api/users/profile/'
        self.user = User.objects.create_user(username='tester', phone='13800138000', password='secret123')

    def token(self, user=None, exp=None):
        user = user or self.user
        return jwt.encode({'user_id': user.pk, 'username': user.username,
                           'exp': exp or datetime.utcnow() + timedelta(days=7)}, settings.SECRET_KEY, algorithm='HS256')

    def test_register_validation_and_hash(self):
        response = self.client.post(self.register, {'username': ' newuser ', 'phone': '13900139000', 'password': 'secret123'}, format='json')
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='newuser')
        self.assertNotEqual(user.password, 'secret123')
        for data in ({'username':'ab','phone':'13900139001','password':'secret123'}, {'username':'abc','phone':'123','password':'secret123'}, {'username':'abc','phone':'13900139002','password':'12345'}):
            self.assertEqual(self.client.post(self.register, data, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.register, {'username':'tester','phone':'13900139003','password':'secret123'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.register, {'username':'other','phone':'13800138000','password':'secret123'}, format='json').status_code, 400)

    def test_login_and_active(self):
        response = self.client.post(self.login, {'username':'tester','password':'secret123'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data['data'])
        self.user.is_active = False; self.user.save()
        self.assertEqual(self.client.post(self.login, {'username':'tester','password':'secret123'}, format='json').status_code, 401)
        self.assertEqual(self.client.post(self.login, {'username':'tester','password':'bad'}, format='json').status_code, 401)

    def test_profile_protection_and_validation(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token())
        self.assertEqual(self.client.get(self.profile).status_code, 200)
        self.assertEqual(self.client.put(self.profile, {'username':'newname','avatar':'https://example.com/a','gender':'F','email':'a@example.com'}, format='json').status_code, 200)
        for field, value in [('is_staff', True), ('is_superuser', True), ('is_active', False), ('phone', '13900139000'), ('password','newpass')]:
            self.assertEqual(self.client.put(self.profile, {field:value}, format='json').status_code, 400)
        self.assertEqual(self.client.put(self.profile, {'email':'bad','gender':'X'}, format='json').status_code, 400)
        self.client.credentials()
        self.assertEqual(self.client.get(self.profile).status_code, 401)

    def test_jwt_failures(self):
        for header in ('Bearer invalid', 'Basic abc', 'Bearer'):
            self.client.credentials(HTTP_AUTHORIZATION=header)
            self.assertEqual(self.client.get(self.profile).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='bearer ' + self.token(exp=datetime.utcnow()-timedelta(seconds=1)))
        self.assertEqual(self.client.get(self.profile).status_code, 401)
        self.user.is_active = False; self.user.save()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token())
        self.assertEqual(self.client.get(self.profile).status_code, 401)
