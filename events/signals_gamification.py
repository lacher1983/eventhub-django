from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Event, Registration, Review, Favorite, UserProfile
from .gamification.core import gamification_engine

User = get_user_model()

@receiver(post_save, sender=Event)
def handle_event_creation(sender, instance, created, **kwargs):
    """Обработка создания мероприятия"""
    if created and instance.organizer:
        gamification_engine.handle_user_action(
            instance.organizer,
            'event_created',
            event_id=instance.id
        )
        
        # Награждаем организатора за создание мероприятия
        gamification_engine.award_points(
            instance.organizer,
            points=15,
            reason=f"Создание мероприятия: {instance.title}"
        )

@receiver(post_save, sender=Registration)
def handle_event_registration(sender, instance, created, **kwargs):
    """Обработка регистрации на мероприятие"""
    if created:
        gamification_engine.handle_user_action(
            instance.user,
            'event_registration',
            event_id=instance.event.id,
            category=instance.event.category.name if instance.event.category else None
        )
        
        # Награждаем пользователя за регистрацию
        gamification_engine.award_points(
            instance.user,
            points=5,
            reason=f"Регистрация на мероприятие: {instance.event.title}"
        )

@receiver(post_save, sender=Review)
def handle_review_creation(sender, instance, created, **kwargs):
    """Обработка создания отзыва"""
    if created:
        gamification_engine.handle_user_action(
            instance.user,
            'review_created',
            event_id=instance.event.id,
            rating=instance.rating
        )
        
        # Награждаем за отзыв
        points = 3 + (instance.rating - 3)  # Больше очков за хорошие отзывы
        gamification_engine.award_points(
            instance.user,
            points=max(points, 1),
            reason=f"Написание отзыва для: {instance.event.title}"
        )

@receiver(post_save, sender=Favorite)
def handle_favorite_added(sender, instance, created, **kwargs):
    """Обработка добавления в избранное"""
    if created:
        gamification_engine.handle_user_action(
            instance.user,
            'add_favorite',
            event_id=instance.event.id
        )
        
        gamification_engine.award_points(
            instance.user,
            points=2,
            reason=f"Добавление в избранное: {instance.event.title}"
        )

@receiver(post_delete, sender=Favorite)
def handle_favorite_removed(sender, instance, **kwargs):
    """Обработка удаления из избранного"""
    # Можно вычитать очки или просто игнорировать
    pass

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание игрового профиля для нового пользователя"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
        
        # Награждаем за регистрацию
        gamification_engine.award_points(
            instance,
            points=10,
            reason="Регистрация на платформе"
        )