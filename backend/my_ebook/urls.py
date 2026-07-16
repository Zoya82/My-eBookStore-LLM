"""
URL configuration for my_ebook project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/',include('apps.users.urls')),  #所有用户接口都以/api/users/开头
    path('api/books/', include('apps.books.urls')),  # 图书接口
    path('api/cart/', include('apps.cart.urls')),   #购物车接口
    path('api/orders/', include('apps.orders.urls')),   #订单接口
    path('api/interactions/', include('apps.interactions.urls')),   #用户交互接口：评价、收藏、浏览历史
    path('api/admin/', include('apps.admin_dashboard.urls')),   #管理员接口

    # ===== Swagger 文档路由 =====
    # 1. 获取 OpenAPI schema（JSON/YAML 格式）
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # 2. Swagger UI 界面（可视化浏览和测试）
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 3. Redoc 界面（另一种文档风格）
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 👇 开发环境下提供 media 文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
