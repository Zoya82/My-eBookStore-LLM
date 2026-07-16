from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.http import Http404
from .models import Review, Favorite, BrowsingHistory
from .serializers import ReviewSerializer, ReviewCreateSerializer, FavoriteSerializer, BrowsingHistorySerializer
from .services import InteractionService
from apps.books.models import Book

def bad(exc): return Response({'code':400,'msg':getattr(exc,'detail',str(exc))},status=400)
def book_id_param(value):
    try: result=int(value)
    except (TypeError,ValueError): raise ValidationError({'book_id':'book_id 必须为正整数'})
    if result < 1: raise ValidationError({'book_id':'book_id 必须为正整数'})
    if not Book.objects.filter(pk=result).exists(): raise Http404('图书不存在')
    return result

class ReviewView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        value=request.query_params.get('book_id')
        try: qs=Review.objects.filter(book_id=book_id_param(value)) if value is not None else Review.objects.filter(user=request.user)
        except ValidationError as e: return bad(e)
        return Response({'code':200,'msg':'success','data':ReviewSerializer(qs.order_by('-created_at'),many=True,context={'request':request}).data})
    def post(self, request):
        serializer=ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid(): return Response({'code':400,'msg':serializer.errors},status=400)
        try: review=InteractionService.create_review(request.user,**serializer.validated_data)
        except Http404 as e: return Response({'code':404,'msg':str(e)},status=404)
        except ValidationError as e: return bad(e)
        return Response({'code':200,'msg':'评价成功','data':ReviewSerializer(review,context={'request':request}).data})

class MyReviewsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({'code':200,'msg':'success','data':ReviewSerializer(Review.objects.filter(user=request.user).order_by('-created_at'),many=True,context={'request':request}).data})

class FavoriteToggleView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        try: book_id=book_id_param(request.data.get('book_id')); result=InteractionService.toggle_favorite(request.user,book_id)
        except ValidationError as e: return bad(e)
        except Http404 as e: return Response({'code':404,'msg':str(e)},status=404)
        return Response({'code':200,'msg':'success','data':result})

class MyFavoritesView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try: value=request.query_params.get('book_id'); qs=Favorite.objects.filter(user=request.user); qs=qs.filter(book_id=book_id_param(value)) if value is not None else qs
        except ValidationError as e: return bad(e)
        return Response({'code':200,'msg':'success','data':FavoriteSerializer(qs.order_by('-created_at'),many=True).data})

class BrowsingHistoryView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({'code':200,'msg':'success','data':BrowsingHistorySerializer(BrowsingHistory.objects.filter(user=request.user).order_by('-created_at','-id')[:20],many=True).data})
    def post(self,request):
        try: book_id=book_id_param(request.data.get('book_id')); history=InteractionService.add_browsing_history(request.user,book_id)
        except ValidationError as e: return bad(e)
        except Http404 as e: return Response({'code':404,'msg':str(e)},status=404)
        return Response({'code':200,'msg':'记录成功','data':BrowsingHistorySerializer(history).data})
    def delete(self,request): return Response({'code':200,'msg':'清空成功','data':{'deleted_count':InteractionService.clear_browsing_history(request.user)}})
