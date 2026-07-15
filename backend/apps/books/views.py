from decimal import Decimal, InvalidOperation

from rest_framework import viewsets, status, filters
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Case, IntegerField, OuterRef, Subquery, Value, When, Q
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from .models import Book
from .serializers import BookListSerializer, BookDetailSerializer
from .utils import BookContentError, get_book_content, get_preview_content, has_readable_content


@extend_schema_view(
    list=extend_schema(
        summary="图书列表",
        description="支持搜索（书名/作者/ISBN）、筛选（分类/出版社）、排序（销量/价格/评分）、新书筛选（is_new=true）",
        parameters=[
            OpenApiParameter(name='search', location='query', required=False, type=str, description='搜索关键词'),
            OpenApiParameter(name='category', location='query', required=False, type=int, description='分类ID'),
            OpenApiParameter(name='publisher', location='query', required=False, type=str, description='出版社'),
            OpenApiParameter(name='is_new', location='query', required=False, type=bool, description='是否新书（true/false）'),
            OpenApiParameter(name='price_min', location='query', required=False, type=str, description='最低售价，必须是有限数字'),
            OpenApiParameter(name='price_max', location='query', required=False, type=str, description='最高售价，必须是有限数字'),
            OpenApiParameter(name='ordering', location='query', required=False, type=str, description='排序字段，如 -sale_price, sales_count'),
            OpenApiParameter(name='page', location='query', required=False, type=int, description='页码'),
            OpenApiParameter(name='page_size', location='query', required=False, type=int, description='每页数量'),
        ],
        responses={200: OpenApiResponse(description='成功返回图书列表')}
    ),
    retrieve=extend_schema(
        summary="图书详情",
        description="返回图书完整信息，已购买电子版的用户可查看已下架图书",
        responses={200: OpenApiResponse(description='成功返回图书详情')}
    ),
    home=extend_schema(
        summary="首页聚合数据",
        description="返回新书上架和热门推荐，用于首页展示",
        responses={200: OpenApiResponse(description='成功返回首页数据')}
    ),
    preview=extend_schema(
        summary="试读",
        description="登录用户可阅读图书全文的前10%，需登录",
        responses={
            200: OpenApiResponse(description='成功返回试读内容'),
            400: OpenApiResponse(description='图书已下架或无试读内容'),
            401: OpenApiResponse(description='未登录'),
        }
    ),
    read_full=extend_schema(
        summary="阅读全文",
        description="仅限已购买电子版的用户阅读全文，不受图书下架影响",
        responses={
            200: OpenApiResponse(description='成功返回全文内容'),
            403: OpenApiResponse(description='未购买该电子书'),
            401: OpenApiResponse(description='未登录'),
        }
    ),
)
class BookViewSet(viewsets.ReadOnlyModelViewSet):
    """图书视图集"""
    queryset = Book.objects.filter(is_on_sale=True).order_by('-id')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'author', 'isbn']
    filterset_fields = ['category', 'publisher']

    def get_annotated_queryset(self):
        representative_version = self.get_queryset_representative_version()
        return Book.objects.filter(is_on_sale=True).annotate(
            representative_sale_price=Subquery(representative_version.values('sale_price')[:1]),
            representative_stock=Subquery(representative_version.values('stock')[:1]),
        )

    def get_queryset(self):
        queryset = self.get_annotated_queryset()
        if self.action in ('retrieve', 'read_full') and self.request.user.is_authenticated:
            from apps.orders.models import DigitalBookPurchase
            purchased_ids = DigitalBookPurchase.objects.filter(user=self.request.user).values('book_id')
            queryset = Book.objects.filter(Q(is_on_sale=True) | Q(pk__in=purchased_ids)).annotate(
                representative_sale_price=Subquery(self.get_queryset_representative_version().values('sale_price')[:1]),
                representative_stock=Subquery(self.get_queryset_representative_version().values('stock')[:1]),
            )

        is_new = self.request.GET.get('is_new')
        if is_new and is_new.lower() == 'true':
            seven_days_ago = timezone.now().date() - timedelta(days=7)
            queryset = queryset.filter(on_shelf_date__gte=seven_days_ago)

        price_min = self.parse_price_filter('price_min')
        price_max = self.parse_price_filter('price_max')
        if price_min is not None:
            queryset = queryset.filter(representative_sale_price__gte=price_min)
        if price_max is not None:
            queryset = queryset.filter(representative_sale_price__lte=price_max)

        ordering = self.request.GET.get('ordering')
        if ordering:
            return self.apply_ordering(queryset, ordering)

        return queryset.order_by('-id')

    def parse_price_filter(self, field_name):
        value = self.request.GET.get(field_name)
        if value is None or value == '':
            return None
        try:
            price = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({field_name: '价格必须是有效数字。'})
        if not price.is_finite():
            raise ValidationError({field_name: '价格必须是有限数字。'})
        return price

    def get_queryset_representative_version(self):
        from .models import BookVersion

        return BookVersion.objects.filter(
            book=OuterRef('pk'),
            is_on_sale=True,
            version_type__in=['physical', 'digital'],
        ).order_by(
            Case(
                When(version_type='physical', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            '-sale_price',
            '-id',
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BookDetailSerializer

    def apply_ordering(self, queryset, ordering):
        mapping = {
            'sale_price': 'representative_sale_price',
            '-sale_price': '-representative_sale_price',
            'sales_count': 'sales_count',
            '-sales_count': '-sales_count',
            'rating': 'rating',
            '-rating': '-rating',
            'publish_date': 'publish_date',
            '-publish_date': '-publish_date',
        }

        if ordering in mapping:
            return queryset.order_by(mapping[ordering])

        return queryset.order_by('-id')

    def retrieve(self, request, *args, **kwargs):
        book = self.get_object()

        if not book.is_on_sale:
            user = request.user
            if user.is_authenticated:
                from apps.orders.models import DigitalBookPurchase
                has_purchased = DigitalBookPurchase.objects.filter(user=user, book=book).exists()
                if has_purchased:
                    serializer = self.get_serializer(book)
                    return Response({
                        'code': 200,
                        'msg': '您已购买该书电子版，可继续阅读',
                        'data': serializer.data
                    })
            from rest_framework.exceptions import NotFound
            raise NotFound('该图书已下架')

        serializer = self.get_serializer(book)
        return Response({'code': 200, 'msg': 'success', 'data': serializer.data})

    @action(detail=True, methods=['get'], url_path='preview', permission_classes=[IsAuthenticated])
    def preview(self, request, pk=None):
        book = self.get_object()

        if not book.is_on_sale:
            return Response({'code': 400, 'msg': '该图书已下架，无法试读'}, status=status.HTTP_400_BAD_REQUEST)

        if not book.content_file_path:
            return Response({'code': 400, 'msg': '本书暂无试读内容'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            preview_content, total_length, preview_length = get_preview_content(book)
        except BookContentError as exc:
            return Response({'code': 400, 'msg': str(exc)}, status=400)

        return Response({
            'code': 200,
            'msg': 'success',
            'data': {
                'book_id': book.id,
                'book_title': book.title,
                'content': preview_content,
                'total_length': total_length,
                'preview_length': preview_length,
                'is_complete': preview_length >= total_length
            }
        })

    @action(detail=True, methods=['get'], url_path='read', permission_classes=[IsAuthenticated])
    def read_full(self, request, pk=None):
        book = self.get_object()

        from apps.orders.models import DigitalBookPurchase
        if not DigitalBookPurchase.objects.filter(user=request.user, book=book).exists():
            return Response({
                'code': 403,
                'msg': '您尚未购买该书的电子版，请先购买'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            content = get_book_content(book)
        except BookContentError as exc:
            return Response({'code': 400, 'msg': str(exc)}, status=400)

        return Response({
            'code': 200,
            'msg': 'success',
            'data': {
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'content': content,
                'total_length': len(content)
            }
        })

    @action(detail=False, methods=['get'], url_path='home')
    def home(self, request):
        queryset = self.get_annotated_queryset()

        new_books = queryset.order_by('-on_shelf_date', '-created_at')[:10]
        hot_books = queryset.order_by('-sales_count')[:10]

        return Response({
            'code': 200,
            'msg': 'success',
            'data': {
                'banners': [],
                'new_books': BookListSerializer(new_books, many=True).data,
                'hot_books': BookListSerializer(hot_books, many=True).data
            }
        })
