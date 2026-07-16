from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),   # 注册接口
    path('login/', views.LoginView.as_view(), name='login'),            #登录接口
    path('profile/', views.ProfileView.as_view(), name='profile'),      #个人信息接口
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
]
