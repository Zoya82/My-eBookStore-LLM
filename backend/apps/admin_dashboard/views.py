from django.db.models import Q, Count, Sum
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import OrderDetailSerializer
from apps.orders.services import OrderService
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.books.models import Book, BookVersion, Category
from .permissions import IsStaffOrSuperuser
from .serializers import AdminOrderActionSerializer, AdminOrderListSerializer, AdminUserToggleSerializer, AdminBookReadSerializer, AdminBookWriteSerializer, AdminBookSaleSerializer, AdminCategorySerializer, AdminRecentOrderSerializer


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


class AdminCategoryListView(AdminBaseView):
    def get(self, request):
        return Response({'code': 200, 'msg': 'success', 'data': AdminCategorySerializer(Category.objects.select_related('parent').all().order_by('sort', 'id'), many=True).data})


class AdminBookListCreateView(AdminBaseView):
    def get(self, request):
        queryset = Book.objects.select_related('category').prefetch_related('versions').all().order_by('-id')
        keyword = request.query_params.get('keyword', '').strip()
        if keyword: queryset = queryset.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword) | Q(isbn__icontains=keyword))
        raw_category = request.query_params.get('category')
        raw_sale = request.query_params.get('is_on_sale')
        try: page = int(request.query_params.get('page', 1)); page_size = int(request.query_params.get('page_size', 20))
        except (TypeError, ValueError): return validation_response({'page': ['参数格式不正确']})
        if raw_category not in (None, ''):
            try: queryset = queryset.filter(category_id=int(raw_category))
            except (TypeError, ValueError): return validation_response({'category': ['category 必须为有效整数']})
        if raw_sale not in (None, ''):
            if raw_sale not in ('true', 'false'): return validation_response({'is_on_sale': ['仅支持 true 或 false']})
            queryset = queryset.filter(is_on_sale=raw_sale == 'true')
        if page < 1: return validation_response({'page': ['page 必须大于等于 1']})
        if not 1 <= page_size <= 100: return validation_response({'page_size': ['page_size 必须在 1 到 100 之间']})
        total = queryset.count(); items = queryset[(page - 1) * page_size: page * page_size]
        return Response({'code': 200, 'msg': 'success', 'data': {'total': total, 'page': page, 'page_size': page_size, 'items': AdminBookReadSerializer(items, many=True).data}})
    def post(self, request):
        serializer = AdminBookWriteSerializer(data=request.data)
        if not serializer.is_valid(): return validation_response(serializer.errors)
        try:
            with transaction.atomic():
                versions = serializer.validated_data.pop('versions')
                book = Book.objects.create(**serializer.validated_data)
                BookVersion.objects.bulk_create([BookVersion(book=book, **item) for item in versions])
        except IntegrityError: return validation_response({'isbn': ['ISBN 已存在']})
        return Response({'code': 201, 'msg': '创建成功', 'data': AdminBookReadSerializer(Book.objects.select_related('category').prefetch_related('versions').get(pk=book.pk)).data}, status=status.HTTP_201_CREATED)


class AdminBookDetailView(AdminBaseView):
    def get_book(self, book_id): return get_object_or_404(Book.objects.select_related('category').prefetch_related('versions'), id=book_id)
    def get(self, request, book_id): return Response({'code': 200, 'msg': 'success', 'data': AdminBookReadSerializer(self.get_book(book_id)).data})
    def put(self, request, book_id):
        book = self.get_book(book_id); serializer = AdminBookWriteSerializer(book, data=request.data, partial=True)
        if not serializer.is_valid(): return validation_response(serializer.errors)
        try:
            with transaction.atomic():
                locked = Book.objects.select_for_update().get(pk=book.pk); versions = serializer.validated_data.pop('versions', None)
                for field, value in serializer.validated_data.items(): setattr(locked, field, value)
                locked.save()
                if versions is not None:
                    existing = {item.version_type: item for item in BookVersion.objects.select_for_update().filter(book=locked)}
                    for item in versions:
                        version = existing.get(item['version_type'])
                        if version:
                            for field, value in item.items(): setattr(version, field, value)
                            version.save()
                        else: BookVersion.objects.create(book=locked, **item)
        except IntegrityError: return validation_response({'isbn': ['ISBN 已存在']})
        return Response({'code': 200, 'msg': '更新成功', 'data': AdminBookReadSerializer(self.get_book(book_id)).data})


class AdminBookSaleView(AdminBaseView):
    def put(self, request, book_id):
        serializer = AdminBookSaleSerializer(data=request.data)
        if not serializer.is_valid(): return validation_response(serializer.errors)
        book = get_object_or_404(Book, id=book_id); book.is_on_sale = serializer.validated_data['is_on_sale']; book.save(update_fields=['is_on_sale', 'updated_at'])
        detail = Book.objects.select_related('category').prefetch_related('versions').get(pk=book.pk)
        return Response({'code': 200, 'msg': '图书已上架' if book.is_on_sale else '图书已下架', 'data': AdminBookReadSerializer(detail).data})


class AdminDashboardSummaryView(AdminBaseView):
    """经营概览；paid_amount 是模拟支付订单状态的金额，不代表真实支付网关到账金额。"""
    def get(self, request):
        user_counts = User.objects.aggregate(total=Count('id'), active=Count('id', filter=Q(is_active=True)), disabled=Count('id', filter=Q(is_active=False)), staff=Count('id', filter=Q(is_staff=True) | Q(is_superuser=True), distinct=True))
        book_counts = Book.objects.aggregate(total=Count('id'), on_sale=Count('id', filter=Q(is_on_sale=True)), off_sale=Count('id', filter=Q(is_on_sale=False)))
        version_counts = BookVersion.objects.aggregate(digital_versions=Count('id', filter=Q(version_type='digital')), physical_versions=Count('id', filter=Q(version_type='physical')))
        order_counts = Order.objects.aggregate(total=Count('id'), pending=Count('id', filter=Q(status=Order.STATUS_PENDING)), submitted=Count('id', filter=Q(status=Order.STATUS_SUBMITTED)), shipped=Count('id', filter=Q(status=Order.STATUS_SHIPPED)), completed=Count('id', filter=Q(status=Order.STATUS_COMPLETED)), cancelled=Count('id', filter=Q(status=Order.STATUS_CANCELLED)))
        paid_statuses = [Order.STATUS_SUBMITTED, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED]
        paid = Order.objects.filter(status__in=paid_statuses).aggregate(paid_order_count=Count('id'), paid_amount=Sum('pay_amount'))
        quantities = OrderItem.objects.filter(order__status__in=paid_statuses).aggregate(physical_quantity=Sum('quantity', filter=Q(version_type='physical')), digital_quantity=Sum('quantity', filter=Q(version_type='digital')))
        low_stock = [{'version_id': item.id, 'book_id': item.book_id, 'book_title': item.book.title, 'stock': item.stock, 'is_on_sale': item.is_on_sale} for item in BookVersion.objects.select_related('book').filter(version_type='physical', is_on_sale=True, stock__lte=10).order_by('stock', 'id')[:10]]
        recent = Order.objects.select_related('user').order_by('-created_at')[:5]
        return Response({'code': 200, 'msg': 'success', 'data': {'users': user_counts, 'books': {**book_counts, **version_counts}, 'orders': order_counts, 'sales': {'paid_order_count': paid['paid_order_count'] or 0, 'paid_amount': format(paid['paid_amount'] or 0, '.2f'), 'physical_quantity': quantities['physical_quantity'] or 0, 'digital_quantity': quantities['digital_quantity'] or 0}, 'low_stock': low_stock, 'recent_orders': AdminRecentOrderSerializer(recent, many=True).data}})
