from django.db import models

# Create your models here.
from django.conf import settings


class Order(models.Model):
    """订单主表"""

    # 订单状态常量（用整数表示，方便排序和比较）
    STATUS_PENDING = 1      # 待付款
    STATUS_SUBMITTED = 2    # 已提交（已付款，待发货）
    STATUS_SHIPPED = 3      # 已发货（待收货）
    STATUS_COMPLETED = 4    # 已完成
    STATUS_CANCELLED = 5    # 已取消

    STATUS_CHOICES = [
        (STATUS_PENDING, '待付款'),
        (STATUS_SUBMITTED, '已提交'),
        (STATUS_SHIPPED, '待收货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
    ]

    # 订单基本信息
    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单编号')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name='下单用户')

    # 收货信息（快照，不从地址表关联，避免地址被修改影响历史订单）
    receiver = models.CharField(max_length=50, verbose_name='收货人')
    receiver_phone = models.CharField(max_length=11, verbose_name='收货人手机号')
    receiver_address = models.CharField(max_length=200, verbose_name='收货详细地址')

    # 金额信息
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单总金额')
    pay_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='实付金额')  # 可扩展优惠券，目前等于总金额

    # 状态与时间
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='订单状态')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    ship_time = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')
    receive_time = models.DateTimeField(null=True, blank=True, verbose_name='收货时间')
    cancel_time = models.DateTimeField(null=True, blank=True, verbose_name='取消时间')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='下单时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 物流信息
    express_no = models.CharField(max_length=50, blank=True, null=True, verbose_name='快递单号')
    express_company = models.CharField(max_length=50, blank=True, null=True, verbose_name='快递公司')

    # 备注
    remark = models.TextField(blank=True, null=True, verbose_name='订单备注')

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']  # 默认按创建时间倒序

    def __str__(self):
        return f'{self.order_no} - {self.user.username}'

    @property
    def status_text(self):
        """获取状态的中文描述"""
        return dict(self.STATUS_CHOICES).get(self.status, '未知')


class OrderItem(models.Model):
    """订单明细表（商品快照）"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='所属订单')

    # 关联的图书ID（方便跳转，但不作为外键约束，避免图书删除影响订单）
    book_id = models.IntegerField(verbose_name='图书ID')
    # 快照字段（下单时复制图书信息，后续图书修改不影响已生成订单）
    book_title = models.CharField(max_length=200, verbose_name='图书名称')
    book_cover = models.URLField(max_length=500, blank=True, null=True, verbose_name='封面图')
    book_author = models.CharField(max_length=100, verbose_name='作者')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='下单时售价')
    quantity = models.PositiveIntegerField(verbose_name='数量')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='小计')

    version_type = models.CharField(
        max_length=10,
        choices=[('digital', '电子版'), ('physical', '纸质版')],
        verbose_name='版本类型'
    )
    class Meta:
        db_table = 'order_items'
        verbose_name = '订单明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.book_title} x {self.quantity}'

class DigitalBookPurchase(models.Model):
    """用户已购买的电子书（永久授权，不受下架影响）"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='digital_purchases')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='digital_purchases')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='digital_purchases')
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'digital_book_purchases'
        verbose_name = '电子书购买记录'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_digital_book')
        ]

    def __str__(self):
        return f'{self.user.username} - {self.book.title}'