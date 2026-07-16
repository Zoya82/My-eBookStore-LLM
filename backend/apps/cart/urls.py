from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name='cart-list'),                    # 获取列表 / 添加商品
    path('batch/', views.CartBatchView.as_view(), name='cart-batch'),        # 批量操作
    path('clear-invalid/', views.CartClearInvalidView.as_view(), name='cart-clear-invalid'),  # 清理失效
    path('<int:item_id>/', views.CartItemView.as_view(), name='cart-item'),  # 单个商品操作
]