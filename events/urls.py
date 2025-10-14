from django.urls import path, include
from . import views
from .views import EventsMapView
from .api import views as api_views
from .views import (
    EventListView, EventDetailView, EventCreateView, 
    EventUpdateView, EventDeleteView, EventSearchView,
    OrganizerDashboardView, EventCalendarView, FavoriteListView,
    register, custom_logout, confirm_email,
    subscription_settings, notifications,
    event_statistics, platform_statistics,
    CombinedEventsView, ArchiveEventsView, ExternalEventsView,
    
    # Добавляем вьюхи для страниц футера из основного views.py
    FAQView, ContactView, PrivacyPolicyView, TermsOfUseView, 
    RefundPolicyView, AboutView, BlogView, CareersView, PressView,
    OrganizerSolutionsView, OrganizerGuidelinesView, OrganizerResourcesView,
    PricingView, SuccessStoriesView, PartnersView, APIDocsView, SitemapView
)
from .views_cart import checkout
from .views_cart import cart_detail, cart_add, cart_remove, cart_update, payment, payment_success, payment_cancel, checkout
from . import views_gamification


urlpatterns = [
    # Основные маршруты мероприятий
    path('', EventListView.as_view(), name='event_list'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/new/', EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    # path('map-test/', views.map_test_view, name='map_test'),
    path('map/', views.EventsMapView.as_view(), name='events_map'),
    path('api/events/map/', views.events_map_api, name='events_map_api'),

    # Регистрации пользователя
    path('register/', register, name='register'),
    path('my-registrations/', views.user_registrations, name='user_registrations'),
    path('event/<int:pk>/register/', views.register_for_event, name='event_register'),
    path('confirm-email/<uuid:confirmation_code>/', confirm_email, name='confirm_email'),

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
    path('checkout/', checkout, name='checkout'),
    
    # Подписки и уведомления
    path('subscriptions/', subscription_settings, name='subscription_settings'),
    path('notifications/', notifications, name='notifications'),

    # Статистика
    path('event/<int:pk>/stats/', event_statistics, name='event_statistics'),
    path('platform-stats/', platform_statistics, name='platform_statistics'),

    # Объединенные мероприятия
    path('events/combined/', CombinedEventsView.as_view(), name='combined_events'),
    path('archive/', ArchiveEventsView.as_view(), name='archive'),

    # Новые URLs для внешних мероприятий
    path('external/', ExternalEventsView.as_view(), name='external_events'),

    # API endpoints для мероприятий
    path('api/events/', api_views.EventListAPI.as_view(), name='events_api'),

    # СИСТЕМУ ПОПУТЧИКОВ
    # path('travel-buddies/', views.TravelBuddiesView.as_view(), name='travel_buddies'),
    # path('travel-buddies/my-requests/', views.my_buddy_requests, name='my_buddy_requests'),
    # path('event/<int:event_id>/create-buddy-request/', views.CreateBuddyRequestView.as_view(), name='create_buddy_request'),
    # path('event/<int:event_id>/create-buddy-group/', views.CreateBuddyGroupView.as_view(), name='create_buddy_group'),
    # path('group/<int:group_id>/chat/', views.GroupChatView.as_view(), name='group_chat'),
    # path('group/<int:group_id>/join/', views.join_group, name='join_group'),
    # path('group/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    # path('buddy-request/<int:request_id>/delete/', views.delete_buddy_request, name='delete_buddy_request'),

        
    # Геймификация
    path('api/gamification/progress/', views_gamification.user_progress, name='user_progress'),
    path('api/gamification/leaderboard/', views_gamification.leaderboard, name='leaderboard'),
    path('api/gamification/quests/<int:quest_id>/claim/', views_gamification.claim_quest_reward, name='claim_quest_reward'),
    
    # Страницы геймификации
    path('profile/game/', views.GameProfileView.as_view(), name='game_profile'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard_page'),

    # Footer странички - КОМПАНИЯ
    path('about/', AboutView.as_view(), name='about'),
    path('blog/', BlogView.as_view(), name='blog'),
    path('careers/', CareersView.as_view(), name='careers'),
    path('press/', PressView.as_view(), name='press'),
    path('contact/', ContactView.as_view(), name='contact'),

    # Footer странички - ПОДДЕРЖКА
    path('support/faq/', FAQView.as_view(), name='faq'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-use/', TermsOfUseView.as_view(), name='terms_of_use'),
    path('legal/refund-policy/', RefundPolicyView.as_view(), name='refund_policy'),
    
    # Footer странички - ОРГАНИЗАТОРАМ
    path('organizers/solutions/', OrganizerSolutionsView.as_view(), name='organizer_solutions'),
    path('organizers/resources/', OrganizerResourcesView.as_view(), name='organizer_resources'),
    path('organizers/guidelines/', OrganizerGuidelinesView.as_view(), name='organizer_guidelines'),
    path('organizers/pricing/', PricingView.as_view(), name='pricing'),
    path('organizers/success-stories/', SuccessStoriesView.as_view(), name='success_stories'),
    path('partners/', PartnersView.as_view(), name='partners'),
    path('api/docs/', APIDocsView.as_view(), name='api_docs'),
    path('sitemap/', SitemapView.as_view(), name='sitemap'),
]