import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
import numpy as np
from .models import Event, Registration, User, Category

class AdvancedAnalytics:
    """Продвинутая аналитика и визуализация данных"""
    
    def __init__(self):
        plt.style.use('dark_background')
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    def generate_user_engagement_metrics(self, days=30):
        """Метрики вовлеченности пользователей"""
        start_date = timezone.now() - timedelta(days=days)
        
        data = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(
                Q(registrations__registration_date__gte=start_date) |
                Q(favorites__created_at__gte=start_date) |
                Q(reviews__registration_date__gte=start_date)
            ).distinct().count(),
            'new_registrations': Registration.objects.filter(
                registration_date__gte=start_date
            ).count(),
            'popular_categories': self._get_popular_categories(days),
            'user_retention': self._calculate_retention_rate(days),
        }
        
        return data
    
    def _get_popular_categories(self, days):
        """Самые популярные категории"""
        start_date = timezone.now() - timedelta(days=days)
        
        categories = Category.objects.annotate(
            event_count=Count('event', filter=Q(event__created_at__gte=start_date)),
            registration_count=Count('event__registrations', 
                                   filter=Q(event__registrations__registration_date__gte=start_date)),
            avg_rating=Avg('event__reviews__rating')
        ).order_by('-registration_count')[:10]
        
        return [
            {
                'name': cat.name,
                'events': cat.event_count,
                'registrations': cat.registration_count,
                'avg_rating': cat.avg_rating or 0
            }
            for cat in categories
        ]
    
    def _calculate_retention_rate(self, days):
        """Расчет retention rate"""
        # Упрощенный расчет retention
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=days)
        ).count()
        
        return (active_users / total_users * 100) if total_users > 0 else 0
    
    def create_engagement_chart(self):
        """График вовлеченности пользователей"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Данные за последние 7 дней
        dates = [timezone.now() - timedelta(days=i) for i in range(7, 0, -1)]
        daily_registrations = []
        daily_active_users = []
        
        for date in dates:
            next_day = date + timedelta(days=1)
            registrations = Registration.objects.filter(
                registration_date__gte=date,
                registration_date__lt=next_day
            ).count()
            daily_registrations.append(registrations)
            
            active_users = User.objects.filter(
                Q(registrations__registration_date__gte=date) |
                Q(last_login__gte=date)
            ).distinct().count()
            daily_active_users.append(active_users)
        
        # График регистраций
        ax1.plot([d.strftime('%d.%m') for d in dates], daily_registrations, 
                marker='o', linewidth=2, color=self.colors[0])
        ax1.set_title('📈 Регистрации по дням', fontsize=14, pad=20)
        ax1.set_ylabel('Количество регистраций')
        ax1.grid(True, alpha=0.3)
        
        # График активных пользователей
        ax2.bar([d.strftime('%d.%m') for d in dates], daily_active_users,
               color=self.colors[1], alpha=0.8)
        ax2.set_title('👥 Активные пользователи', fontsize=14, pad=20)
        ax2.set_ylabel('Количество пользователей')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_category_analysis_chart(self):
        """Анализ категорий мероприятий"""
        categories = Category.objects.annotate(
            total_events=Count('event'),
            total_registrations=Count('event__registrations'),
            avg_rating=Avg('event__reviews__rating')
        ).order_by('-total_registrations')[:8]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Круговой график распределения мероприятий
        category_names = [cat.name for cat in categories]
        event_counts = [cat.total_events for cat in categories]
        
        ax1.pie(event_counts, labels=category_names, autopct='%1.1f%%',
               colors=self.colors, startangle=90)
        ax1.set_title('📊 Распределение мероприятий по категориям')
        
        # Столбчатый график регистраций
        registration_counts = [cat.total_registrations for cat in categories]
        y_pos = np.arange(len(category_names))
        
        ax2.barh(y_pos, registration_counts, color=self.colors[2])
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(category_names)
        ax2.set_xlabel('Количество регистраций')
        ax2.set_title('🎫 Популярность категорий')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig):
        """Конвертация matplotlib figure в base64"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png)
        return f"data:image/png;base64,{graphic.decode('utf-8')}"

# Глобальный экземпляр аналитики
advanced_analytics = AdvancedAnalytics()