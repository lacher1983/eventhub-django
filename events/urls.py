from django.urls import path, include
from django.conf import settings
from .views import (
    EventListView, EventDetailView, EventCreateView, 
    EventUpdateView, EventDeleteView, 
    EventCalendarView, OrganizerDashboardView, FavoriteListView,
    register_for_event, user_registrations, ad_click, ad_impression,
    toggle_favorite, add_to_cart, cart_view, update_cart_item,
    remove_from_cart, debug_cart, checkout, payment, order_success
)

app_name = 'events'

urlpatterns = [
    # Главная страница
    path('', EventListView.as_view(), name='event_list'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/new/', EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    
    # Регистрация и пользовательские функции
    path('event/<int:pk>/register/', register_for_event, name='event_register'),
    path('my-registrations/', user_registrations, name='user_registrations'),
    
    # Реклама
    path('ads/click/<int:ad_id>/', ad_click, name='ad_click'),
    path('ads/impression/<int:ad_id>/', ad_impression, name='ad_impression'),
    
    # Календарь и дашборд
    path('calendar/', EventCalendarView.as_view(), name='event_calendar'),
    path('dashboard/', OrganizerDashboardView.as_view(), name='organizer_dashboard'),
    
    # Избранное
    path('favorites/', FavoriteListView.as_view(), name='favorite_list'),
    path('event/<int:event_id>/favorite/', toggle_favorite, name='toggle_favorite'),
    
    # Корзина и заказы
    path('cart/add/<int:event_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('debug/cart/', debug_cart, name='debug_cart'),
    path('checkout/', checkout, name='checkout'),
    path('payment/', payment, name='payment'),
    path('order/success/<int:order_id>/', order_success, name='order_success'),
    
    # API
    path('api/', include('events.api.urls')),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns