from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderView.as_view(), name='order-list'),           # 列表 / 创建
    path('<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),  # 详情 / 操作
    path('bookshelf/', views.MyBookshelfView.as_view(), name='bookshelf'),  #电子书架
]