from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, FavoriteViewSet, ReviewViewSet, RegistrationViewSet
from . import views

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'favorites', FavoriteViewSet, basename='favorites')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'registrations', RegistrationViewSet, basename='registrations')

urlpatterns = router.urls