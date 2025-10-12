import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    
    def send_notification(self, message, event=None):
        """Отправка уведомления в Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not set")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            if event:
                message = f"🎉 {message}\n\n📅 {event.title}\n📍 {event.location}\n🕐 {event.date.strftime('%d.%m.%Y %H:%M')}"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

# Использование в views.py
def send_event_telegram_notification(event, action="created"):
    """Отправка уведомления о мероприятии в Telegram"""
    notifier = TelegramNotifier()
    
    actions = {
        'created': '🎊 Новое мероприятие создано!',
        'updated': '📝 Мероприятие обновлено',
        'registration': '✅ Новая регистрация на мероприятие'
    }
    
    message = f"{actions.get(action, '🔔 Уведомление')}\n\n"
    message += f"<b>{event.title}</b>\n"
    message += f"📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n"
    message += f"📍 {event.location}\n"
    message += f"💰 {event.price}₽" if event.price > 0 else "🎫 Бесплатно"
    
    return notifier.send_notification(message)