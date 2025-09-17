from rest_framework import viewsets
from ..models import Registration
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Event, Favorite, Review
from .serializers import EventSerializer, FavoriteSerializer, ReviewSerializer, RegistrationSerializer
from rest_framework import generics

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """API для мероприятий"""
    queryset = Event.objects.filter(is_active=True).select_related('category')
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'event_type']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """Добавить/удалить из избранного"""
        event = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            event=event
        )
        
        if not created:
            favorite.delete()
            return Response({'status': 'removed'})
        
        return Response({'status': 'added'})

class FavoriteViewSet(viewsets.ModelViewSet):
    """API для избранных мероприятий"""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('event')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    """API для отзывов"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).select_related('event')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EventListAPIView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Event.objects.filter(is_active=True)

class RegistrationCreateAPIView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)