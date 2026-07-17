from django.db import models
from django.utils import timezone
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='分类名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父级分类')
    sort = models.IntegerField(default=0, verbose_name='排序')
    description = models.TextField(blank=True, default='', verbose_name='分类说明')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'categories'
        verbose_name = '图书分类'

    def __str__(self):
        return self.name


class Book(models.Model):
    """图书主表"""
    # 基本信息
    title = models.CharField(max_length=200, verbose_name='书名')
    author = models.CharField(max_length=100, verbose_name='作者')
    isbn = models.CharField(max_length=20, unique=True, verbose_name='ISBN编号')
    publisher = models.CharField(max_length=100, verbose_name='出版社')
    publish_date = models.DateField(null=True, blank=True, verbose_name='出版日期')

    # 展示信息
    cover_image = models.URLField(max_length=500, blank=True, null=True, verbose_name='封面图')
    description = models.TextField(blank=True, null=True, verbose_name='简介')
    catalog = models.TextField(blank=True, null=True, verbose_name='目录')

    # 全文内容（存储文件路径，相对于 MEDIA_ROOT）
    content_file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name='全文文件路径')

    # 分类
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books', verbose_name='所属分类')

    # 状态与统计
    is_on_sale = models.BooleanField(default=True, verbose_name='是否上架')
    sales_count = models.IntegerField(default=0, verbose_name='总销量')
    rating = models.FloatField(default=0.0, verbose_name='平均评分')
    on_shelf_date = models.DateField(default=timezone.now, verbose_name='上架日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = models.Manager()

    class Meta:
        db_table = 'books'
        verbose_name = '图书'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['title', 'author']),
            models.Index(fields=['isbn']),
        ]

    def __str__(self):
        return self.title

    def get_digital_version(self):
        return self.versions.filter(version_type='digital', is_on_sale=True).first()

    def get_physical_version(self):
        return self.versions.filter(version_type='physical', is_on_sale=True).first()

    @property
    def has_content(self):
        """是否有全文内容"""
        return bool(self.content_file_path)


class BookVersion(models.Model):
    """图书版本表：电子版/纸质版"""
    VERSION_TYPES = [
        ('digital', '电子版'),
        ('physical', '纸质版'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='versions', verbose_name='所属图书')
    version_type = models.CharField(max_length=10, choices=VERSION_TYPES, verbose_name='版本类型')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='定价')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='售价')
    stock = models.IntegerField(default=99999 if version_type == 'digital' else 0, verbose_name='库存')
    is_on_sale = models.BooleanField(default=True, verbose_name='是否在售')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = 'book_versions'
        verbose_name = '图书版本'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(fields=['book', 'version_type'], name='unique_book_version_type')
        ]

    def __str__(self):
        return f'{self.book.title} - {self.get_version_type_display()}'
