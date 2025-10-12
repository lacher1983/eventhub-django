from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .telegram_bot import TelegramNotifier
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.telegram_notifier = TelegramNotifier()

    def send_event_notification(self, user, event, notification_type, context=None):
        """Отправка уведомления о мероприятии"""
        context = context or {}
        
        # Email уведомление
        self._send_email_notification(user, event, notification_type, context)
        
        # Telegram уведомление (если настроено)
        self._send_telegram_notification(user, event, notification_type, context)
        
        # Внутреннее уведомление
        self._create_internal_notification(user, event, notification_type)
    
    def _send_email_notification(self, user, event, notification_type, context):
        """Отправка email уведомления"""
        try:
            subject_map = {
                'registration': f'✅ Подтверждение регистрации на {event.title}',
                'reminder': f'🔔 Напоминание: {event.title} скоро начнется',
                'cancellation': f'❌ Отмена мероприятия {event.title}',
                'new_event': f'🎉 Новое мероприятие: {event.title}',
                'registration_confirmed': f'🎫 Регистрация подтверждена: {event.title}'
            }
            
            template_map = {
                'registration': 'events/emails/registration_confirmation.html',
                'reminder': 'events/emails/event_reminder.html',
                'cancellation': 'events/emails/event_cancellation.html',
                'new_event': 'events/emails/new_event_notification.html',
                'registration_confirmed': 'events/emails/registration_confirmed.html'
            }
            
            subject = subject_map.get(notification_type, 'Уведомление EventHub')
            template = template_map.get(notification_type, 'events/emails/notification.html')
            
            context.update({
                'user': user,
                'event': event,
                'type': notification_type,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            })
            
            html_message = render_to_string(template, context)
            plain_message = f"{subject}\n\n{event.title}\n{event.date.strftime('%d.%m.%Y %H:%M')}\n{event.location}"
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email notification sent to {user.email} for {notification_type}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _send_telegram_notification(self, user, event, notification_type, context):
        """Отправка Telegram уведомления"""
        try:
            message_templates = {
                'registration': f'🎟️ Новая регистрация на мероприятие!\n{event.title}',
                'reminder': f'⏰ Напоминание: {event.title} через 24 часа!',
                'new_event': f'🚀 Новое мероприятие создано!\n{event.title}',
            }
            
            message = message_templates.get(notification_type)
            if message:
                self.telegram_notifier.send_notification(message, event)
                
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    def _create_internal_notification(self, user, event, notification_type):
        """Создание внутреннего уведомления"""
        try:
            from .models import Notification
            Notification.objects.create(
                user=user,
                event=event,
                message=f"Уведомление: {notification_type}"
            )
        except Exception as e:
            logger.error(f"Failed to create internal notification: {e}")
    
    def send_bulk_notifications(self, users, event, notification_type):
        """Массовая отправка уведомлений"""
        for user in users:
            self.send_event_notification(user, event, notification_type)

# Глобальный экземпляр сервиса уведомлений
notification_service = NotificationService()