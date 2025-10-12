from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .telegram_bot import TelegramNotifier
import logging
from datetime import timedelta
from .models import Notification, User

logger = logging.getLogger(__name__)

class EnhancedNotificationService:
    """Улучшенная система уведомлений с персонализацией"""
    
    def __init__(self):
        self.telegram_notifier = TelegramNotifier()
        self.notification_templates = self._load_templates()
    
    def _load_templates(self):
        """Загрузка шаблонов уведомлений"""
        return {
            'registration': {
                'email_subject': '🎟️ Подтверждение регистрации на {event_title}',
                'telegram_template': '🎊 Новая регистрация!\n{event_title}\n📅 {event_date}',
                'push_template': 'Вы зарегистрированы на {event_title}'
            },
            'reminder_24h': {
                'email_subject': '⏰ Напоминание: {event_title} через 24 часа!',
                'telegram_template': '🔔 Через 24 часа: {event_title}',
                'push_template': 'Напоминание: {event_title} завтра'
            },
            'reminder_1h': {
                'email_subject': '🔔 Скоро начинается: {event_title}',
                'telegram_template': '🚀 Через 1 час: {event_title}',
                'push_template': 'Мероприятие начинается через 1 час'
            },
            'weather_alert': {
                'email_subject': '🌤️ Погода для {event_title}',
                'telegram_template': '🌤️ Погода на мероприятие: {weather_info}',
                'push_template': 'Погодное уведомление для мероприятия'
            },
            'buddy_match': {
                'email_subject': '👥 Найден попутчик для {event_title}',
                'telegram_template': '👥 Найден попутчик!\n{event_title}',
                'push_template': 'Найден попутчик для мероприятия'
            }
        }
    
    def send_personalized_notification(self, user, event, notification_type, context=None):
        """Персонализированное уведомление с учетом предпочтений пользователя"""
        context = context or {}
        
        # Определяем предпочтительный канал уведомлений
        preferred_channels = self._get_user_notification_preferences(user)
        
        # Персонализируем контент
        personalized_context = self._personalize_content(user, event, notification_type, context)
        
        # Отправляем через предпочтительные каналы
        for channel in preferred_channels:
            try:
                if channel == 'email' and user.email:
                    self._send_personalized_email(user, event, notification_type, personalized_context)
                
                elif channel == 'telegram':
                    self._send_personalized_telegram(user, event, notification_type, personalized_context)
                
                elif channel == 'push':
                    self._send_internal_notification(user, event, notification_type, personalized_context)
                    
            except Exception as e:
                logger.error(f"Failed to send {channel} notification to {user.username}: {e}")
    
    def _get_user_notification_preferences(self, user):
        """Получение предпочтений пользователя по уведомлениям"""
        # В реальной системе это бы хранилось в настройках пользователя
        # Здесь упрощенная логика
        default_preferences = ['email', 'internal']
        
        # Если пользователь активен в Telegram, добавляем его
        if hasattr(user, 'telegram_chat_id') and user.telegram_chat_id:
            default_preferences.append('telegram')
        
        return default_preferences
    
    def _personalize_content(self, user, event, notification_type, context):
        """Персонализация контента уведомления"""
        personalized = context.copy()
        
        # Добавляем имя пользователя
        personalized['user_name'] = user.first_name or user.username
        
        # Персонализируем в зависимости от типа уведомления
        if notification_type == 'reminder_24h':
            # Добавляем персонализированные рекомендации
            personalized['personal_tips'] = self._get_personal_event_tips(user, event)
        
        elif notification_type == 'weather_alert':
            # Добавляем погодные рекомендации
            personalized['weather_recommendations'] = self._get_weather_recommendations(
                context.get('weather_data', {})
            )
        
        return personalized
    
    def _get_personal_event_tips(self, user, event):
        """Персонализированные советы для мероприятия"""
        tips = []
        
        # На основе предыдущих мероприятий пользователя
        past_events = Registration.objects.filter(
            user=user,
            event__category=event.category
        ).select_related('event')[:3]
        
        if past_events:
            tips.append(f"На основе вашего опыта в {event.category.name}")
        
        # На основе отзывов
        user_reviews = Review.objects.filter(user=user)
        if user_reviews.exists():
            avg_rating = user_reviews.aggregate(Avg('rating'))['rating__avg']
            if avg_rating and avg_rating < 3:
                tips.append("Рекомендуем внимательнее выбирать мероприятия")
        
        return tips
    
    def send_bulk_smart_notifications(self, users, event, notification_type):
        """Умная массовая рассылка с оптимизацией времени отправки"""
        optimal_times = self._calculate_optimal_send_times(users)
        
        for user in users:
            optimal_time = optimal_times.get(user.id, timezone.now())
            
            # Если оптимальное время в будущем, планируем отправку
            if optimal_time > timezone.now():
                self._schedule_notification(user, event, notification_type, optimal_time)
            else:
                self.send_personalized_notification(user, event, notification_type)
    
    def _calculate_optimal_send_times(self, users):
        """Расчет оптимального времени отправки для каждого пользователя"""
        optimal_times = {}
        
        for user in users:
            # Анализируем активность пользователя
            user_activity = self._analyze_user_activity_pattern(user)
            optimal_time = user_activity.get('best_notification_time', timezone.now())
            optimal_times[user.id] = optimal_time
        
        return optimal_times
    
    def _analyze_user_activity_pattern(self, user):
        """Анализ паттернов активности пользователя"""
        # Анализируем время последних активностей
        recent_activities = []
        
        # Логины
        if user.last_login:
            recent_activities.append(user.last_login.hour)
        
        # Регистрации на мероприятия
        recent_registrations = Registration.objects.filter(
            user=user,
            registration_date__gte=timezone.now() - timedelta(days=30)
        )
        for reg in recent_registrations:
            recent_activities.append(reg.registration_date.hour)
        
        # Определяем наиболее активные часы
        if recent_activities:
            best_hour = max(set(recent_activities), key=recent_activities.count)
            optimal_time = timezone.now().replace(
                hour=best_hour, minute=0, second=0, microsecond=0
            )
            
            # Если лучшее время уже прошло сегодня, планируем на завтра
            if optimal_time < timezone.now():
                optimal_time += timedelta(days=1)
        else:
            # Дефолтное время - 10 утра
            optimal_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
            if optimal_time < timezone.now():
                optimal_time += timedelta(days=1)
        
        return {'best_notification_time': optimal_time}

# Глобальный экземпляр улучшенного сервиса уведомлений
enhanced_notification_service = EnhancedNotificationService()