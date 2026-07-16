from rest_framework import serializers
from .models import Review, Favorite, BrowsingHistory
from apps.books.serializers import BookListSerializer

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_detail = BookListSerializer(source='book', read_only=True)
    is_mine = serializers.SerializerMethodField()
    class Meta:
        model = Review
        fields = ['id','user','username','book','book_title','book_detail','rating','comment','created_at','updated_at','is_mine']
        read_only_fields = ['id','user','book','created_at','updated_at','is_mine']
    def get_is_mine(self, obj): return bool(self.context.get('request') and self.context['request'].user == obj.user)

class ReviewCreateSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(required=True, min_value=1)
    rating = serializers.IntegerField(required=True, min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    def validate_comment(self, value): return value.strip()

class FavoriteSerializer(serializers.ModelSerializer):
    book_detail = BookListSerializer(source='book', read_only=True)
    book_is_on_sale = serializers.BooleanField(source='book.is_on_sale', read_only=True)
    class Meta:
        model = Favorite
        fields = ['id','book','book_detail','book_is_on_sale','created_at']

class BrowsingHistorySerializer(serializers.ModelSerializer):
    book_detail = BookListSerializer(source='book', read_only=True)
    book_is_on_sale = serializers.BooleanField(source='book.is_on_sale', read_only=True)
    class Meta:
        model = BrowsingHistory
        fields = ['id','book','book_detail','book_is_on_sale','created_at']
