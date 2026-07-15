from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.serializers import OrderDetailSerializer
from apps.orders.services import OrderService
from apps.users.models import User
from apps.users.serializers import UserSerializer
from .permissions import IsStaffOrSuperuser
from .serializers import AdminOrderActionSerializer, AdminOrderListSerializer, AdminUserToggleSerializer


def validation_response(errors, msg='提交信息有误'):
    return Response({'code': 400, 'msg': msg, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)


class AdminBaseView(APIView):
    permission_classes = [IsStaffOrSuperuser]


class AdminOrderListView(AdminBaseView):
    def get(self, request):
        queryset = Order.objects.all().prefetch_related('items').order_by('-created_at')
        raw_status = request.query_params.get('status', '').strip()
        if raw_status:
            try: order_status = int(raw_status)
            except ValueError: return validation_response({'status': ['参数格式不正确']})
            if order_status not in dict(Order.STATUS_CHOICES): return validation_response({'status': ['不支持的订单状态']})
            queryset = queryset.filter(status=order_status)
        for field in ('order_no', 'receiver'):
            value = request.query_params.get(field, '').strip()
            if value: queryset = queryset.filter(**{f'{field}__icontains': value})
        return Response({'code': 200, 'msg': 'success', 'data': AdminOrderListSerializer(queryset, many=True).data})


class AdminOrderDetailView(AdminBaseView):
    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
        return Response({'code': 200, 'msg': 'success', 'data': OrderDetailSerializer(order).data})


class AdminOrderActionView(AdminBaseView):
    def put(self, request, order_id):
        serializer = AdminOrderActionSerializer(data=request.data)
        if not serializer.is_valid(): return validation_response(serializer.errors)
        order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
        action = serializer.validated_data['action']
        if action == 'ship':
            if order.status != Order.STATUS_SUBMITTED: return validation_response({'action': ['当前订单状态不允许发货']})
            if not order.items.filter(version_type='physical').exists(): return validation_response({'action': ['订单不包含纸质版商品']})
            try:
                order = OrderService.ship_order(order.user, order.id, serializer.validated_data['express_no'], serializer.validated_data['express_company'])
            except ValidationError as error: return validation_response(error.detail)
            msg = '发货成功'
        else:
            try: order = OrderService.cancel_order(order.user, order.id)
            except ValidationError as error: return validation_response(error.detail)
            msg = '订单已取消'
        return Response({'code': 200, 'msg': msg, 'data': OrderDetailSerializer(order).data})


class AdminUserListView(AdminBaseView):
    def get(self, request):
        keyword = request.query_params.get('keyword', '').strip()
        try:
            page = int(request.query_params.get('page', 1)); page_size = int(request.query_params.get('page_size', 20))
        except (TypeError, ValueError): return validation_response({'page': ['参数格式不正确']})
        if page < 1: return validation_response({'page': ['page 必须大于等于 1']})
        if not 1 <= page_size <= 100: return validation_response({'page_size': ['page_size 必须在 1 到 100 之间']})
        queryset = User.objects.all().order_by('-date_joined')
        if keyword: queryset = queryset.filter(Q(username__icontains=keyword) | Q(phone__icontains=keyword))
        total = queryset.count(); items = queryset[(page - 1) * page_size:page * page_size]
        return Response({'code': 200, 'msg': 'success', 'data': {'total': total, 'page': page, 'page_size': page_size, 'items': UserSerializer(items, many=True).data}})


class AdminUserDetailView(AdminBaseView):
    def get(self, request, user_id):
        return Response({'code': 200, 'msg': 'success', 'data': UserSerializer(get_object_or_404(User, id=user_id)).data})


class AdminUserToggleView(AdminBaseView):
    def put(self, request, user_id):
        serializer = AdminUserToggleSerializer(data=request.data)
        if not serializer.is_valid(): return validation_response(serializer.errors)
        user = get_object_or_404(User, id=user_id)
        if user.id == request.user.id: return validation_response({'user_id': ['不能禁用当前管理员自己']})
        if user.is_superuser and not request.user.is_superuser: return validation_response({'user_id': ['不能操作超级管理员账号']})
        user.is_active = serializer.validated_data['is_active']; user.save(update_fields=['is_active'])
        return Response({'code': 200, 'msg': '用户已启用' if user.is_active else '用户已禁用', 'data': {'user_id': user.id, 'username': user.username, 'is_active': user.is_active}})
