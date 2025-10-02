from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

@shared_task
def send_event_reminders():
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    events = Event.objects.filter(date__date=tomorrow.date())
    
    for event in events:
        registrations = event.registrations.all()
        for registration in registrations:
            send_mail(
                f'Напоминание: {event.title}',
                f'Мероприятие состоится завтра в {event.date.time()}',
                'noreply@eventhub.com',
                [registration.user.email]
            )