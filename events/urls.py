from django.urls import path, include
from . import views
from .views import (
    EventListView, EventDetailView, EventCreateView, 
    EventUpdateView, EventDeleteView, EventSearchView,
    OrganizerDashboardView, EventCalendarView, FavoriteListView,
    register, custom_logout, confirm_email,
    subscription_settings, notifications,
    event_statistics, platform_statistics
)
from .views_cart import cart_detail, cart_add, cart_remove, cart_update, payment, payment_success, payment_cancel

urlpatterns = [
    # Основные маршруты мероприятий
    path('', EventListView.as_view(), name='event_list'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/new/', EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    
    # Регистрации пользователя
    path('register/', register, name='register'),
    path('my-registrations/', views.user_registrations, name='user_registrations'),
    path('event/<int:pk>/register/', views.register_for_event, name='event_register'),
    path('confirm-email/<uuid:confirmation_code>/', confirm_email, name='confirm_email'),# подтверждение регистрации

    # Реклама
    path('ads/click/<int:ad_id>/', views.ad_click, name='ad_click'),
    path('ads/impression/<int:ad_id>/', views.ad_impression, name='ad_impression'),
    
    # Календарь
    path('calendar/', EventCalendarView.as_view(), name='event_calendar'),
    
    # API
    path('api/', include('events.api.urls')),
    
    # Дашборд организатора
    path('dashboard/', OrganizerDashboardView.as_view(), name='organizer_dashboard'),
    
    # Избранное
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_list'),
    path('event/<int:event_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # Отзывы
    path('event/<int:event_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    
    # Корзина и оплата
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:event_id>/', cart_add, name='cart_add'),
    path('cart/remove/<int:event_id>/', cart_remove, name='cart_remove'),
    path('cart/update/<int:event_id>/', cart_update, name='cart_update'),
    path('payment/', payment, name='payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),

    # Подписки и уведомления
    path('subscriptions/', subscription_settings, name='subscription_settings'),
    path('notifications/', notifications, name='notifications'),

    # Статистика
    path('event/<int:pk>/stats/', event_statistics, name='event_statistics'),
    path('platform-stats/', platform_statistics, name='platform_statistics'),
]