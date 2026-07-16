#用户数据表
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    """自定义用户模型（扩展 Django 自带 User 表）"""
    phone = models.CharField(max_length=11, unique=True, blank=True, null=True, verbose_name='手机号')
    avatar = models.URLField(blank=True, null=True, verbose_name='头像链接')
    gender = models.CharField(max_length=2, choices=[('M', '男'), ('F', '女')], blank=True, null=True, verbose_name='性别')

    # 下面这两行是新增的，解决冲突
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Address(models.Model):
    """收货地址表"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='所属用户')
    receiver = models.CharField(max_length=50, verbose_name='收货人')
    phone = models.CharField(max_length=11, verbose_name='收货人手机号')
    province = models.CharField(max_length=50, verbose_name='省')
    city = models.CharField(max_length=50, verbose_name='市')
    district = models.CharField(max_length=50, verbose_name='区')
    detail = models.CharField(max_length=200, verbose_name='详细地址')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    class Meta:
        db_table = 'addresses'
        verbose_name = '收货地址'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.receiver} - {self.phone}'