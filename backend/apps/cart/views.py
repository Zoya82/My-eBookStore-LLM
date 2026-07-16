from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Cart
from .serializers import CartSerializer, CartAddSerializer, CartUpdateSerializer
from .services import CartService


class CartView(APIView):
    """购物车列表与添加"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="获取购物车列表",
        description="返回当前用户购物车所有商品，包含勾选总价和失效商品数量",
        responses={
            200: OpenApiResponse(description='成功返回购物车列表'),
            401: OpenApiResponse(description='未登录'),
        }
    )
    def get(self, request):
        items = Cart.objects.filter(user=request.user).select_related('book').order_by('-created_at')
        serializer = CartSerializer(items, many=True)

        total_price = CartService.get_selected_total(request.user)
        invalid_items = CartService.get_invalid_items(request.user)

        return Response({
            'items': serializer.data,
            'selected_total': total_price,
            'invalid_count': len(invalid_items),
            'invalid_items': CartSerializer(invalid_items, many=True).data
        })

    @extend_schema(
        summary="添加商品到购物车",
        description="支持选择电子版或纸质版，会自动校验库存",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'book_id': {'type': 'integer', 'example': 1},
                    'version_type': {'type': 'string', 'enum': ['digital', 'physical'], 'example': 'physical'},
                    'quantity': {'type': 'integer', 'example': 1}
                },
                'required': ['book_id']
            }
        },
        responses={
            200: OpenApiResponse(description='添加成功'),
            400: OpenApiResponse(description='参数错误或库存不足'),
            401: OpenApiResponse(description='未登录'),
        }
    )
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartService.add_to_cart(
                request.user,
                serializer.validated_data['book_id'],
                serializer.validated_data.get('version_type', 'physical'),
                serializer.validated_data['quantity']
            )
            return Response({
                'code': 200,
                'msg': '添加成功',
                'data': CartSerializer(cart_item).data
            })
        except Exception as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CartItemView(APIView):
    """单个购物车商品操作"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="修改购物车商品数量",
        description="修改指定购物车条目的数量，会校验库存上限",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'quantity': {'type': 'integer', 'example': 3}
                },
                'required': ['quantity']
            }
        },
        responses={
            200: OpenApiResponse(description='修改成功'),
            400: OpenApiResponse(description='参数错误或库存不足'),
            401: OpenApiResponse(description='未登录'),
            404: OpenApiResponse(description='购物车条目不存在'),
        }
    )
    def put(self, request, item_id):
        serializer = CartUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartService.update_quantity(
                request.user,
                item_id,
                serializer.validated_data['quantity']
            )
            return Response({
                'code': 200,
                'msg': '修改成功',
                'data': CartSerializer(cart_item).data
            })
        except Exception as e:
            return Response({'code': 400, 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="删除单个购物车商品",
        description="删除指定的购物车条目",
        responses={
            200: OpenApiResponse(description='删除成功'),
            401: OpenApiResponse(description='未登录'),
            404: OpenApiResponse(description='购物车条目不存在'),
        }
    )
    def delete(self, request, item_id):
        CartService.delete_items(request.user, [item_id])
        return Response({'code': 200, 'msg': '删除成功'})


class CartBatchView(APIView):
    """购物车批量操作"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="批量删除购物车商品",
        description="根据ID列表批量删除购物车条目",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'item_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2, 3]}
                },
                'required': ['item_ids']
            }
        },
        responses={
            200: OpenApiResponse(description='删除成功'),
            400: OpenApiResponse(description='请选择要删除的商品'),
            401: OpenApiResponse(description='未登录'),
        }
    )
    def delete(self, request):
        item_ids = request.data.get('item_ids', [])
        if not item_ids:
            return Response({'code': 400, 'msg': '请选择要删除的商品'}, status=status.HTTP_400_BAD_REQUEST)

        CartService.delete_items(request.user, item_ids)
        return Response({'code': 200, 'msg': '删除成功'})

    @extend_schema(
        summary="批量切换商品勾选状态",
        description="批量勾选或取消勾选购物车商品，用于结算前选择",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'item_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2]},
                    'is_selected': {'type': 'boolean', 'example': True}
                },
                'required': ['item_ids', 'is_selected']
            }
        },
        responses={
            200: OpenApiResponse(description='操作成功'),
            400: OpenApiResponse(description='请选择商品'),
            401: OpenApiResponse(description='未登录'),
        }
    )
    def post(self, request):
        item_ids = request.data.get('item_ids', [])
        is_selected = request.data.get('is_selected', True)

        if not item_ids:
            return Response({'code': 400, 'msg': '请选择商品'}, status=status.HTTP_400_BAD_REQUEST)

        CartService.toggle_selected(request.user, item_ids, is_selected)
        return Response({'code': 200, 'msg': '操作成功'})


class CartClearInvalidView(APIView):
    """清理失效商品"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="清理失效商品",
        description="自动识别并删除购物车中已下架或库存为0的商品",
        responses={
            200: OpenApiResponse(description='清理成功'),
            401: OpenApiResponse(description='未登录'),
        }
    )
    def delete(self, request):
        invalid_items = CartService.get_invalid_items(request.user)
        ids = [item.id for item in invalid_items]
        CartService.delete_items(request.user, ids)
        return Response({'code': 200, 'msg': f'已清理 {len(ids)} 件失效商品'})