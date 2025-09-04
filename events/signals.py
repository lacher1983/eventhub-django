from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event

@receiver(post_save, sender=Event)
def notify_subscribers(sender, instance, created, **kwargs):
    if created:
        from .tasks import send_event_notification
        send_event_notification.delay(instance.id)