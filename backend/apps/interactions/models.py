from django.db import models

# Create your models here.
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """图书评价表（用户只能评价已购买的图书）"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews',
                             verbose_name='评价用户')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='reviews', verbose_name='评价图书')

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='评分（1~5星）'
    )
    comment = models.TextField(blank=True, null=True, verbose_name='评价内容')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='评价时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'reviews'
        verbose_name = '图书评价'
        verbose_name_plural = verbose_name
        # 同一个用户对同一本书只能评价一次
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_review')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 评价 {self.book.title} - {self.rating}星'


class Favorite(models.Model):
    """图书收藏表"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites',
                             verbose_name='收藏用户')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='favorited_by',
                             verbose_name='收藏图书')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')

    class Meta:
        db_table = 'favorites'
        verbose_name = '图书收藏'
        verbose_name_plural = verbose_name
        # 同一个用户对同一本书只能收藏一次
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_favorite')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 收藏了 {self.book.title}'


class BrowsingHistory(models.Model):
    """浏览历史表（只保留最近20条）"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='browsing_histories',
                             verbose_name='浏览用户')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='browsed_by', verbose_name='浏览图书')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='浏览时间')

    class Meta:
        db_table = 'browsing_histories'
        verbose_name = '浏览历史'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 浏览了 {self.book.title}'