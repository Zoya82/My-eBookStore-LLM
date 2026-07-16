from django.urls import path
from . import views

urlpatterns = [
    # 订单管理
    path('orders/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('orders/<int:order_id>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('orders/<int:order_id>/action/', views.AdminOrderActionView.as_view(), name='admin-order-action'),

    # 用户管理
    path('users/', views.AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:user_id>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<int:user_id>/toggle/', views.AdminUserToggleView.as_view(), name='admin-user-toggle'),

    path('categories/', views.AdminCategoryListView.as_view(), name='admin-category-list'),
    path('books/', views.AdminBookListCreateView.as_view(), name='admin-book-list-create'),
    path('books/<int:book_id>/', views.AdminBookDetailView.as_view(), name='admin-book-detail'),
    path('books/<int:book_id>/sale/', views.AdminBookSaleView.as_view(), name='admin-book-sale'),
    path('dashboard/summary/', views.AdminDashboardSummaryView.as_view(), name='admin-dashboard-summary'),
]
