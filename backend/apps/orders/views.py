from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Order, DigitalBookPurchase
from .serializers import OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer
from .services import OrderService
from apps.books.utils import has_readable_content

def error_response(exc):
    detail = getattr(exc, 'detail', str(exc)); return Response({'code': 400, 'msg': detail}, status=400)

class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = Order.objects.filter(user=request.user).prefetch_related('items')
        value = request.query_params.get('status')
        if value is not None:
            try: value = int(value)
            except ValueError: return Response({'code': 400, 'msg': '状态参数格式错误'}, status=400)
            if value not in dict(Order.STATUS_CHOICES): return Response({'code': 400, 'msg': '不支持的状态值'}, status=400)
            qs = qs.filter(status=value)
        return Response({'code': 200, 'msg': 'success', 'data': OrderListSerializer(qs, many=True).data})
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid(): return Response({'code': 400, 'msg': serializer.errors}, status=400)
        try:
            order = OrderService.create_order(request.user, serializer.validated_data['address'], serializer.validated_data['receiver'], serializer.validated_data['phone'], serializer.validated_data['cart_item_ids'], serializer.validated_data.get('remark', ''))
            return Response({'code': 200, 'msg': '订单创建成功，请尽快支付', 'data': OrderDetailSerializer(order).data})
        except ValidationError as exc: return error_response(exc)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get_order(self, request, order_id):
        try: return Order.objects.prefetch_related('items').get(id=order_id, user=request.user)
        except Order.DoesNotExist: return None
    def get(self, request, order_id):
        order = self.get_order(request, order_id)
        if not order: return Response({'code': 404, 'msg': '订单不存在'}, status=404)
        return Response({'code': 200, 'msg': 'success', 'data': OrderDetailSerializer(order).data})
    def put(self, request, order_id):
        action = request.data.get('action')
        if action not in {'pay','cancel','confirm'}: return Response({'code': 400, 'msg': '不支持的操作类型'}, status=400)
        try:
            order = {'pay': OrderService.pay_order, 'cancel': OrderService.cancel_order, 'confirm': OrderService.confirm_receive}[action](request.user, order_id)
            return Response({'code': 200, 'msg': '操作成功', 'data': OrderDetailSerializer(order).data})
        except ValidationError as exc: return error_response(exc)
        except Order.DoesNotExist: return Response({'code': 404, 'msg': '订单不存在'}, status=404)

class MyBookshelfView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        purchases = DigitalBookPurchase.objects.filter(user=request.user).select_related('book').order_by('-purchased_at')
        data = []
        for purchase in purchases:
            readable = has_readable_content(purchase.book)
            data.append({'book_id': purchase.book_id, 'title': purchase.book.title, 'author': purchase.book.author, 'cover_image': purchase.book.cover_image, 'purchased_at': purchase.purchased_at, 'can_read': readable, 'has_content': readable, 'is_on_sale': purchase.book.is_on_sale})
        return Response({'code': 200, 'msg': 'success', 'data': data})
