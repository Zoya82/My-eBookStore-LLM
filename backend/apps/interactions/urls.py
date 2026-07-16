from django.urls import path
from . import views

urlpatterns = [
    # 评价
    path('reviews/', views.ReviewView.as_view(), name='review-list-create'),
    path('reviews/me/', views.MyReviewsView.as_view(), name='my-reviews'),

    # 收藏
    path('favorites/toggle/', views.FavoriteToggleView.as_view(), name='favorite-toggle'),
    path('favorites/', views.MyFavoritesView.as_view(), name='my-favorites'),

    # 浏览历史
    path('histories/', views.BrowsingHistoryView.as_view(), name='browsing-history'),
]