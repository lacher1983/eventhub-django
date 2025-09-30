from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import EmailConfirmation
from .models import Event

User = get_user_model()

@receiver(post_save, sender=Event)
def create_email_confirmation(sender, instance, created, **kwargs):
    if created:
        EmailConfirmation.objects.create(user=instance)

@receiver(post_save, sender=Event)
def notify_subscribers(sender, instance, created, **kwargs):
    if created and instance.is_active:
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

def send_event_notification(user, event):
    """Отправка уведомления о новом мероприятии"""
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
        None,
        [user.email],
        html_message=html_message,
    )