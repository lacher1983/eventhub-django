from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = router.urls