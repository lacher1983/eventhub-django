import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
import asyncio

class AnalyticsConsumer(AsyncWebsocketConsumer):
    """WebSocket для real-time аналитики"""
    
    async def connect(self):
        await self.accept()
        self.analytics_task = asyncio.create_task(self.send_analytics_updates())
    
    async def disconnect(self, close_code):
        if hasattr(self, 'analytics_task'):
            self.analytics_task.cancel()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'subscribe':
            await self.send_initial_data()
    
    async def send_analytics_updates(self):
        """Периодическая отправка обновлений аналитики"""
        while True:
            try:
                analytics_data = await self.get_realtime_analytics()
                await self.send(text_data=json.dumps({
                    'type': 'analytics_update',
                    'data': analytics_data
                }))
                await asyncio.sleep(10)  # Обновление каждые 10 секунд
            except Exception as e:
                print(f"Analytics error: {e}")
                await asyncio.sleep(30)
    
    @database_sync_to_async
    def get_realtime_analytics(self):
        """Получение real-time аналитики"""
        from .models import Event, Registration, User
        from django.db.models import Count, Q
        import random
        
        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        
        # Real-time метрики
        return {
            'online_users': random.randint(50, 200),  # В реальности - из Redis
            'active_events': Event.objects.filter(
                is_active=True,
                date__gte=now
            ).count(),
            'registrations_last_hour': Registration.objects.filter(
                registration_date__gte=hour_ago
            ).count(),
            'popular_categories': self.get_popular_categories(),
            'live_updates': self.get_live_updates()
        }
    
    def get_popular_categories(self):
        """Популярные категории в реальном времени"""
        from .models import Event
        from django.db.models import Count
        
        return list(Event.objects.filter(
            is_active=True
        ).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5])
    
    def get_live_updates(self):
        """Live обновления (регистрации, новые события)"""
        from .models import Registration, Event
        from django.db.models import Count
        
        recent_registrations = Registration.objects.filter(
            registration_date__gte=timezone.now() - timedelta(minutes=5)
        ).select_related('user', 'event')[:10]
        
        return [
            {
                'type': 'registration',
                'user': reg.user.username,
                'event': reg.event.title,
                'timestamp': reg.registration_date.isoformat()
            }
            for reg in recent_registrations
        ]

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket для real-time уведомлений"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            await self.accept()
            self.notification_task = asyncio.create_task(self.send_notifications())
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'notification_task'):
            self.notification_task.cancel()
    
    async def send_notifications(self):
        """Отправка уведомлений пользователю"""
        while True:
            try:
                notifications = await self.get_user_notifications()
                for notification in notifications:
                    await self.send(text_data=json.dumps({
                        'type': 'notification',
                        'data': notification
                    }))
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Notification error: {e}")
                await asyncio.sleep(30)
    
    @database_sync_to_async
    def get_user_notifications(self):
        """Получение непрочитанных уведомлений"""
        from .models import Notification
        notifications = Notification.objects.filter(
            user=self.user,
            read=False
        )[:5]
        
        result = []
        for notification in notifications:
            result.append({
                'id': notification.id,
                'message': notification.message,
                'type': notification.notification_type,
                'timestamp': notification.sent_at.isoformat()
            })
            notification.read = True
            notification.save()
        
        return result

class EventConsumer(AsyncWebsocketConsumer):
    """WebSocket для real-time обновлений по конкретному мероприятию"""
    
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.event_group_name = f'event_{self.event_id}'
        
        await self.channel_layer.group_add(
            self.event_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Отправляем текущую статистику
        event_data = await self.get_event_data()
        await self.send(text_data=json.dumps({
            'type': 'event_data',
            'data': event_data
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.event_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'get_updates':
            event_data = await self.get_event_data()
            await self.send(text_data=json.dumps({
                'type': 'event_update',
                'data': event_data
            }))
    
    async def event_update(self, event):
        """Обработчик обновлений мероприятия"""
        await self.send(text_data=json.dumps({
            'type': 'event_update',
            'data': event
        }))
    
    @database_sync_to_async
    def get_event_data(self):
        """Получение данных мероприятия"""
        from .models import Event, Registration
        try:
            event = Event.objects.get(id=self.event_id)
            registrations_count = event.registrations.count()
            
            return {
                'id': event.id,
                'title': event.title,
                'registrations_count': registrations_count,
                'available_spots': event.capacity - registrations_count,
                'views_count': getattr(event.eventstatistic, 'views_count', 0),
                'favorites_count': event.favorited_by.count(),
                'live_registrations': self.get_recent_registrations()
            }
        except Event.DoesNotExist:
            return {}
    
    def get_recent_registrations(self):
        """Недавние регистрации"""
        from .models import Registration
        recent = Registration.objects.filter(
            event_id=self.event_id,
            registration_date__gte=timezone.now() - timedelta(hours=1)
        ).select_related('user')[:10]
        
        return [
            {
                'user': reg.user.username,
                'timestamp': reg.registration_date.isoformat()
            }
            for reg in recent
        ]