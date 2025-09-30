from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_event_notification(user, event, notification_type):
    subject_map = {
        'registration': f'Подтверждение регистрации на {event.title}',
        'reminder': f'Напоминание: {event.title} скоро начнется',
        'cancellation': f'Отмена мероприятия {event.title}'
    }
    
    html_message = render_to_string('emails/notification.html', {
        'user': user,
        'event': event,
        'type': notification_type
    })
    
    send_mail(
        subject_map[notification_type],
        '',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message
    )