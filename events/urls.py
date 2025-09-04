from django.urls import path, include
from . import views
from .views import (EventListView, EventDetailView, EventCreateView, 
                    EventUpdateView, EventDeleteView, 
                    EventCalendarView, OrganizerDashboardView, FavoriteListView)

urlpatterns = [
    path('', EventListView.as_view(), name='event_list'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/new/', EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    path('event/<int:pk>/register/', views.register_for_event, name='event_register'),
    path('my-registrations/', views.user_registrations, name='user_registrations'),
    path('ads/click/<int:ad_id>/', views.ad_click, name='ad_click'),
    path('ads/impression/<int:ad_id>/', views.ad_impression, name='ad_impression'),
    path('calendar/', views.EventCalendarView.as_view(), name='event_calendar'),
    path('api/', include('events.api.urls')),
    path('dashboard/', views.OrganizerDashboardView.as_view(), name='organizer_dashboard'),
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_list'),
    path('event/<int:event_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]