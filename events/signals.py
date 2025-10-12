from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import EmailConfirmation, Event, Subscription, Notification, Registration, Review, Favorite
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_email_confirmation(sender, instance, created, **kwargs):
    """Создание подтверждения email при регистрации пользователя"""
    if created:
        EmailConfirmation.objects.get_or_create(user=instance)

@receiver(post_save, sender=Event)
def notify_subscribers(sender, instance, created, **kwargs):
    if created and instance.is_active:
        try:
            # Получаем подписчиков на категорию мероприятия
            subscriptions = Subscription.objects.filter(
                categories=instance.category,
                is_active=True
            ).select_related('user')
        
            for subscription in subscriptions:
                # Создаем уведомление
                Notification.objects.create(
                    user=subscription.user,
                    event=instance
                )
            
                # Отправляем email уведомление
                send_event_notification(subscription.user, instance)
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in notify_subscribers: {e}")

def send_event_notification(user, event):
    """Отправка уведомления о новом мероприятии"""
    try:
        subject = f'Новое мероприятие: {event.title}'
        html_message = render_to_string('events/emails/new_event_notification.html', {
            'user': user,
            'event': event,
            'site_url': 'http://127.0.0.1:8000',
        })
        plain_message = strip_tags(html_message)
    
        send_mail(
            subject,
            plain_message,
            None,  # Используется DEFAULT_FROM_EMAIL
            [user.email],
            html_message=html_message,
            fail_silently=True  # Не прерывать выполнение при ошибке email
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending event notification: {e}")