from datetime import datetime, timedelta
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import User, Address
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, AddressSerializer, ChangePasswordSerializer
from django.shortcuts import get_object_or_404

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'msg': serializer.errors}, status=400)
        try:
            with transaction.atomic():
                user = User.objects.create_user(**serializer.validated_data)
        except IntegrityError:
            return Response({'code': 400, 'msg': '用户名或手机号已存在'}, status=400)
        return Response({'code': 200, 'msg': '注册成功', 'data': UserSerializer(user).data})

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'msg': serializer.errors}, status=400)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            disabled_user = User.objects.filter(username=serializer.validated_data['username']).first()
            if disabled_user and not disabled_user.is_active and disabled_user.check_password(serializer.validated_data['password']):
                return Response({'code': 403, 'msg': '您的账号已被禁用，请联系管理员了解详情'}, status=403)
            return Response({'code': 401, 'msg': '用户名或密码错误'}, status=401)
        payload = {'user_id': user.id, 'username': user.username,
                   'exp': datetime.utcnow() + timedelta(days=7)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response({'code': 200, 'msg': '登录成功',
                         'data': {'token': token, 'user': UserSerializer(user).data}})

class AddressListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')
        return Response({'code': 200, 'msg': 'success', 'data': AddressSerializer(addresses, many=True).data})
    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if not serializer.is_valid(): return Response({'code': 400, 'msg': serializer.errors}, status=400)
        with transaction.atomic():
            first = not Address.objects.filter(user=request.user).exists()
            address = serializer.save(user=request.user, is_default=serializer.validated_data.get('is_default', False) or first)
            if address.is_default: Address.objects.filter(user=request.user).exclude(pk=address.pk).update(is_default=False)
        return Response({'code': 200, 'msg': '地址创建成功', 'data': AddressSerializer(address).data})

class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def _get(self, request, pk): return get_object_or_404(Address, pk=pk, user=request.user)
    def put(self, request, pk):
        address = self._get(request, pk); serializer = AddressSerializer(address, data=request.data, partial=True)
        if not serializer.is_valid(): return Response({'code': 400, 'msg': serializer.errors}, status=400)
        with transaction.atomic():
            address = serializer.save()
            if address.is_default: Address.objects.filter(user=request.user).exclude(pk=address.pk).update(is_default=False)
            elif Address.objects.filter(user=request.user).exclude(pk=address.pk).exists() and not Address.objects.filter(user=request.user, is_default=True).exists(): address.is_default=True; address.save(update_fields=['is_default'])
        return Response({'code': 200, 'msg': '地址更新成功', 'data': AddressSerializer(address).data})
    def delete(self, request, pk):
        address = self._get(request, pk); was_default = address.is_default
        with transaction.atomic():
            address.delete()
            if was_default:
                replacement = Address.objects.filter(user=request.user).order_by('-id').first()
                if replacement: replacement.is_default = True; replacement.save(update_fields=['is_default'])
        return Response({'code': 200, 'msg': '地址删除成功', 'data': None})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'code': 200, 'msg': 'success', 'data': UserSerializer(request.user).data})
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'code': 400, 'msg': serializer.errors}, status=400)
        serializer.save()
        return Response({'code': 200, 'msg': '更新成功', 'data': serializer.data})

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid(): return Response({'code': 400, 'msg': serializer.errors}, status=400)
        if not request.user.check_password(serializer.validated_data['old_password']): return Response({'code': 400, 'msg': '原密码错误'}, status=400)
        request.user.set_password(serializer.validated_data['new_password']); request.user.save()
        return Response({'code': 200, 'msg': '密码修改成功', 'data': None})
