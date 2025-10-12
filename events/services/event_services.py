from django.db import transaction
from django.utils import timezone
from ..models import Event, Registration, Favorite
from django.core.exceptions import ValidationError

class EventService:
    
    @staticmethod
    def create_event(organizer, validated_data):
        """Создание мероприятия с валидацией"""
        with transaction.atomic():
            event = Event.objects.create(organizer=organizer, **validated_data)
            
            # Автоматическая установка is_free если цена 0
            if event.price == 0:
                event.is_free = True
                event.save()
                
            return event
    
    @staticmethod
    def register_for_event(user, event):
        """Регистрация на мероприятие с проверками"""
        if not event.is_active:
            raise ValidationError("Мероприятие не активно")
        
        if event.date < timezone.now():
            raise ValidationError("Мероприятие уже прошло")
        
        if Registration.objects.filter(user=user, event=event).exists():
            raise ValidationError("Вы уже зарегистрированы на это мероприятие")
        
        if event.registrations.count() >= event.capacity:
            raise ValidationError("Нет свободных мест")
        
        return Registration.objects.create(user=user, event=event)
    
    @staticmethod
    def get_similar_events(event, limit=6):
        """Получение похожих мероприятий"""
        from django.db.models import Q
        return Event.objects.filter(
            Q(category=event.category) | Q(event_type=event.event_type),
            is_active=True,
            date__gte=timezone.now()
        ).exclude(pk=event.pk).distinct()[:limit]