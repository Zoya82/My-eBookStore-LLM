from django.db import models
# Create your models here.
from django.conf import settings

class Cart(models.Model):
    """购物车表"""
    # 版本类型常量
    VERSION_DIGITAL = 'digital'
    VERSION_PHYSICAL = 'physical'
    VERSION_CHOICES = [
        (VERSION_DIGITAL, '电子版'),
        (VERSION_PHYSICAL, '纸质版'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='所属用户'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='图书'
    )
    # 👇 新增：记录用户选择的是电子版还是纸质版
    version_type = models.CharField(
        max_length=10,
        choices=VERSION_CHOICES,
        default=VERSION_PHYSICAL,  # 默认纸质版（兼容老数据）
        verbose_name='版本类型'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    is_selected = models.BooleanField(default=True, verbose_name='是否勾选')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cart'
        verbose_name = '购物车'
        verbose_name_plural = verbose_name
        # 约束升级：同一用户 + 同一本书 + 同一版本 唯一
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book', 'version_type'],
                name='unique_user_book_version'
            )
        ]

    def __str__(self):
        username = getattr(self.user, 'username', '未知用户')
        title = getattr(self.book, 'title', '未知图书')
        version_label = dict(self.VERSION_CHOICES).get(self.version_type, '')
        return f'{username} - {title} ({version_label}) x {self.quantity}'

    def get_version(self):
        """获取对应的 BookVersion 对象"""
        return self.book.versions.filter(
            version_type=self.version_type,
            is_on_sale=True
        ).first()

    def subtotal(self):
        """
        计算该商品的小计（版本售价 × 数量）
        """
        version = self.get_version()
        if version:
            return version.sale_price * self.quantity
        # 兼容：如果版本不存在，返回0
        return 0