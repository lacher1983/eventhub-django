from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models

from ..models import Event, Favorite, Review, Registration
from .serializers import EventSerializer, FavoriteSerializer, ReviewSerializer, RegistrationSerializer

from django.db.models import Prefetch


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
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        """Регистрация на мероприятие"""
        event = self.get_object()
        
        # Проверка доступности регистрации
        if not event.is_active:
            return Response(
                {'error': 'Мероприятие не доступно для регистрации'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка доступности билетов
        if event.registrations.count() >= event.capacity:
            return Response(
                {'error': 'Нет свободных мест'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration, created = Registration.objects.get_or_create(
            user=request.user,
            event=event,
            defaults={'status': 'confirmed'}  # Автоматически подтверждаем регистрацию
        )
        
        if not created:
            return Response({
                'status': 'already_registered',
                'registration_id': registration.id
            })
        
        return Response({
            'status': 'registered',
            'registration_id': registration.id,
            'message': 'Регистрация успешно завершена'
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Ближайшие мероприятия"""
        upcoming_events = Event.objects.filter(
            date__gte=timezone.now(),
            is_active=True
        ).select_related('category').order_by('date')[:10]
        
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Популярные мероприятия (по количеству регистраций)"""
        popular_events = Event.objects.filter(
            is_active=True
        ).annotate(
            registrations_count=models.Count('registrations')
        ).order_by('-registrations_count')[:10]
        
        serializer = self.get_serializer(popular_events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def registrations_info(self, request, pk=None):
        """Информация о регистрациях на мероприятие"""
        event = self.get_object()
        registrations_count = event.registrations.count()
        available_spots = event.capacity - registrations_count
        
        return Response({
            'total_registrations': registrations_count,
            'available_spots': available_spots,
            'capacity': event.capacity,
            'is_available': available_spots > 0
        })

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

class RegistrationViewSet(viewsets.ModelViewSet):
    """API для регистраций на мероприятия"""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related('event')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена регистрации"""
        registration = self.get_object()
        registration.delete()
        return Response({'status': 'registration_cancelled'})