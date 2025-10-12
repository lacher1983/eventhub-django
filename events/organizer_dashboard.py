from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from django.core.mail import send_mail
from django.template.loader import render_to_string

class OrganizerDashboard:
    """Расширенная панель управления для организаторов"""
    
    def __init__(self, organizer):
        self.organizer = organizer
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    def get_dashboard_stats(self, days=30):
        """Основная статистика организатора"""
        start_date = timezone.now() - timedelta(days=days)
        
        events = self.organizer.organized_events.filter(
            created_at__gte=start_date
        )
        
        total_events = events.count()
        total_registrations = events.aggregate(
            total=Count('registrations')
        )['total'] or 0
        
        # Доходы (если мероприятия платные)
        total_revenue = events.aggregate(
            revenue=Sum('registrations__event__price')
        )['revenue'] or 0
        
        # Средний рейтинг
        avg_rating = events.aggregate(
            rating=Avg('reviews__rating')
        )['rating'] or 0
        
        # Активные мероприятия
        active_events = events.filter(
            is_active=True,
            date__gte=timezone.now()
        ).count()
        
        return {
            'total_events': total_events,
            'total_registrations': total_registrations,
            'total_revenue': total_revenue,
            'avg_rating': round(avg_rating, 2),
            'active_events': active_events,
            'popular_events': self.get_popular_events(days),
            'registration_trends': self.get_registration_trends(days),
            'audience_analytics': self.get_audience_analytics(days),
            'revenue_analytics': self.get_revenue_analytics(days)
        }
    
    def get_popular_events(self, days=30):
        """Самые популярные мероприятия организатора"""
        start_date = timezone.now() - timedelta(days=days)
        
        popular_events = self.organizer.organized_events.filter(
            created_at__gte=start_date
        ).annotate(
            reg_count=Count('registrations'),
            fav_count=Count('favorited_by'),
            avg_rating=Avg('reviews__rating'),
            view_count=Count('eventstatistic__views_count')
        ).order_by('-reg_count')[:5]
        
        return [
            {
                'id': event.id,
                'title': event.title,
                'registrations': event.reg_count,
                'favorites': event.fav_count,
                'views': event.view_count,
                'rating': event.avg_rating or 0,
                'date': event.date.strftime('%d.%m.%Y'),
                'revenue': event.reg_count * event.price,
                'conversion_rate': round((event.reg_count / event.view_count * 100), 2) if event.view_count > 0 else 0
            }
            for event in popular_events
        ]
    
    def get_registration_trends(self, days=30):
        """Тренды регистраций по дням"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Группируем регистрации по дням
        registrations = self.organizer.organized_events.filter(
            registrations__registration_date__gte=start_date
        ).values('registrations__registration_date__date').annotate(
            count=Count('registrations')
        ).order_by('registrations__registration_date__date')
        
        # Создаем полный временной ряд
        date_range = [start_date + timedelta(days=x) for x in range(days + 1)]
        trend_data = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
        
        for reg in registrations:
            date_str = reg['registrations__registration_date__date'].strftime('%Y-%m-%d')
            if date_str in trend_data:
                trend_data[date_str] = reg['count']
        
        return {
            'dates': list(trend_data.keys()),
            'counts': list(trend_data.values())
        }
    
    def get_audience_analytics(self, days=30):
        """Аналитика аудитории"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Получаем всех участников мероприятий организатора
        attendees = self.organizer.organized_events.filter(
            registrations__registration_date__gte=start_date
        ).values(
            'registrations__user__id',
            'registrations__user__username',
            'registrations__user__date_joined'
        ).distinct()
        
        total_attendees = attendees.count()
        
        # Анализ лояльности
        user_event_counts = self.organizer.organized_events.filter(
            registrations__registration_date__gte=start_date
        ).values('registrations__user').annotate(
            event_count=Count('registrations__event', distinct=True)
        )
        
        repeat_attendees = sum(1 for user in user_event_counts if user['event_count'] > 1)
        loyalty_rate = (repeat_attendees / total_attendees * 100) if total_attendees > 0 else 0
        
        # Анализ новых vs постоянных участников
        new_attendees = attendees.filter(
            registrations__user__date_joined__gte=start_date
        ).count()
        
        returning_attendees = total_attendees - new_attendees
        
        return {
            'total_attendees': total_attendees,
            'new_attendees': new_attendees,
            'returning_attendees': returning_attendees,
            'repeat_attendees': repeat_attendees,
            'loyalty_rate': round(loyalty_rate, 2),
            'engagement_metrics': self.get_engagement_metrics(days)
        }
    
    def get_engagement_metrics(self, days):
        """Метрики вовлеченности"""
        start_date = timezone.now() - timedelta(days=days)
        
        events = self.organizer.organized_events.filter(
            created_at__gte=start_date
        )
        
        total_views = events.aggregate(
            views=Sum('eventstatistic__views_count')
        )['views'] or 0
        
        total_favorites = events.aggregate(
            favorites=Count('favorited_by')
        )['favorites'] or 0
        
        total_reviews = events.aggregate(
            reviews=Count('reviews')
        )['reviews'] or 0
        
        total_registrations = events.aggregate(
            registrations=Count('registrations')
        )['registrations'] or 0
        
        conversion_rate = self.calculate_conversion_rate(days)
        
        return {
            'total_views': total_views,
            'total_favorites': total_favorites,
            'total_reviews': total_reviews,
            'total_registrations': total_registrations,
            'conversion_rate': conversion_rate,
            'engagement_score': self.calculate_engagement_score(days)
        }
    
    def calculate_conversion_rate(self, days):
        """Расчет конверсии просмотров в регистрации"""
        start_date = timezone.now() - timedelta(days=days)
        
        events = self.organizer.organized_events.filter(
            created_at__gte=start_date
        )
        
        total_views = events.aggregate(
            views=Sum('eventstatistic__views_count')
        )['views'] or 0
        
        total_registrations = events.aggregate(
            registrations=Count('registrations')
        )['registrations'] or 0
        
        if total_views > 0:
            return round((total_registrations / total_views) * 100, 2)
        return 0
    
    def calculate_engagement_score(self, days):
        """Расчет общего скора вовлеченности"""
        start_date = timezone.now() - timedelta(days=days)
        
        events = self.organizer.organized_events.filter(
            created_at__gte=start_date
        )
        
        # Собираем различные метрики вовлеченности
        metrics = events.aggregate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
            favorite_count=Count('favorited_by'),
            registration_count=Count('registrations')
        )
        
        # Взвешенная формула для engagement score
        engagement_score = (
            (metrics['avg_rating'] or 0) * 20 +  # Рейтинг (0-100)
            min(metrics['review_count'] * 2, 20) +  # Отзывы
            min(metrics['favorite_count'] * 3, 30) +  # Избранное
            min(metrics['registration_count'], 50)  # Регистрации
        )
        
        return min(engagement_score, 100)  # Ограничиваем 100
    
    def get_revenue_analytics(self, days=30):
        """Аналитика доходов"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Доходы по мероприятиям
        revenue_by_event = self.organizer.organized_events.filter(
            registrations__registration_date__gte=start_date
        ).annotate(
            event_revenue=Sum('registrations__event__price')
        ).values('title', 'event_revenue').order_by('-event_revenue')[:10]
        
        # Ежемесячная динамика доходов
        monthly_revenue = self.organizer.organized_events.filter(
            registrations__registration_date__gte=start_date
        ).extra({
            'month': "EXTRACT(month FROM registrations_registration.registration_date)",
            'year': "EXTRACT(year FROM registrations_registration.registration_date)"
        }).values('year', 'month').annotate(
            revenue=Sum('price')
        ).order_by('year', 'month')
        
        return {
            'revenue_by_event': list(revenue_by_event),
            'monthly_revenue': list(monthly_revenue),
            'projected_revenue': self.calculate_projected_revenue()
        }
    
    def calculate_projected_revenue(self):
        """Прогнозирование доходов на основе текущих трендов"""
        # Упрощенный прогноз на основе средних значений
        recent_events = self.organizer.organized_events.filter(
            created_at__gte=timezone.now() - timedelta(days=90)
        )
        
        if not recent_events.exists():
            return 0
        
        avg_revenue_per_event = recent_events.aggregate(
            avg_revenue=Avg('registrations__event__price')
        )['avg_revenue'] or 0
        
        avg_events_per_month = recent_events.count() / 3  # За 3 месяца
        
        projected_monthly = avg_revenue_per_event * avg_events_per_month
        return round(projected_monthly, 2)
    
    def generate_performance_report(self, days=30):
        """Генерация отчета о производительности"""
        stats = self.get_dashboard_stats(days)
        
        report = {
            'organizer': self.organizer.username,
            'period_days': days,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'summary': {
                'total_events': stats['total_events'],
                'total_registrations': stats['total_registrations'],
                'total_revenue': stats['total_revenue'],
                'average_rating': stats['avg_rating']
            },
            'performance_indicators': {
                'conversion_rate': stats['engagement_metrics']['conversion_rate'],
                'audience_loyalty': stats['audience_analytics']['loyalty_rate'],
                'engagement_score': stats['engagement_metrics']['engagement_score']
            },
            'recommendations': self.generate_recommendations(stats)
        }
        
        return report
    
    def generate_recommendations(self, stats):
        """Генерация рекомендаций для улучшения"""
        recommendations = []
        
        if stats['engagement_metrics']['conversion_rate'] < 5:
            recommendations.append({
                'type': 'conversion',
                'title': 'Улучшите конверсию просмотров в регистрации',
                'description': 'Добавьте более привлекательные описания и фотографии мероприятий',
                'priority': 'high'
            })
        
        if stats['audience_analytics']['loyalty_rate'] < 20:
            recommendations.append({
                'type': 'loyalty',
                'title': 'Повысьте лояльность аудитории',
                'description': 'Создайте программу лояльности для постоянных участников',
                'priority': 'medium'
            })
        
        if stats['avg_rating'] < 4.0:
            recommendations.append({
                'type': 'quality',
                'title': 'Улучшите качество мероприятий',
                'description': 'Проанализируйте отзывы и улучшите организацию мероприятий',
                'priority': 'high'
            })
        
        if stats['total_events'] < 3:
            recommendations.append({
                'type': 'activity',
                'title': 'Увеличьте активность',
                'description': 'Создавайте больше мероприятий для роста аудитории',
                'priority': 'medium'
            })
        
        return recommendations
    
    def create_performance_chart(self, days=30):
        """Создание визуализации производительности"""
        stats = self.get_dashboard_stats(days)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # График 1: Регистрации по дням
        trends = stats['registration_trends']
        ax1.plot(trends['dates'], trends['counts'], marker='o', color=self.colors[0], linewidth=2)
        ax1.set_title('📈 Динамика регистраций', fontsize=14, pad=20)
        ax1.set_ylabel('Количество регистраций')
        ax1.tick_params(axis='x', rotation=45)
        
        # График 2: Распределение по мероприятиям
        popular_events = stats['popular_events']
        event_titles = [event['title'][:20] + '...' for event in popular_events]
        event_registrations = [event['registrations'] for event in popular_events]
        
        ax2.barh(event_titles, event_registrations, color=self.colors[1])
        ax2.set_title('🎯 Популярные мероприятия', fontsize=14, pad=20)
        ax2.set_xlabel('Количество регистраций')
        
        # График 3: Метрики вовлеченности
        engagement_labels = ['Просмотры', 'Избранное', 'Отзывы', 'Регистрации']
        engagement_values = [
            stats['engagement_metrics']['total_views'],
            stats['engagement_metrics']['total_favorites'],
            stats['engagement_metrics']['total_reviews'],
            stats['engagement_metrics']['total_registrations']
        ]
        
        ax3.pie(engagement_values, labels=engagement_labels, autopct='%1.1f%%', 
               colors=self.colors, startangle=90)
        ax3.set_title('📊 Вовлеченность аудитории', fontsize=14, pad=20)
        
        # График 4: KPI показатели
        kpi_labels = ['Конверсия', 'Лояльность', 'Рейтинг']
        kpi_values = [
            stats['engagement_metrics']['conversion_rate'],
            stats['audience_analytics']['loyalty_rate'],
            stats['avg_rating'] * 20  # Нормализуем до 100
        ]
        
        ax4.bar(kpi_labels, kpi_values, color=self.colors[3])
        ax4.set_title('🎯 KPI показатели', fontsize=14, pad=20)
        ax4.set_ylabel('Баллы')
        
        plt.tight_layout()
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png)
        return f"data:image/png;base64,{graphic.decode('utf-8')}"
    
    def send_weekly_report(self):
        """Отправка еженедельного отчета организатору"""
        try:
            report = self.generate_performance_report(7)  # За последние 7 дней
            
            html_message = render_to_string('events/emails/organizer_weekly_report.html', {
                'organizer': self.organizer,
                'report': report,
                'chart_url': self.create_performance_chart(7)
            })
            
            plain_message = f"Отчет за неделю для {self.organizer.username}\n\n"
            plain_message += f"Мероприятий: {report['summary']['total_events']}\n"
            plain_message += f"Регистраций: {report['summary']['total_registrations']}\n"
            plain_message += f"Доход: {report['summary']['total_revenue']} руб.\n"
            plain_message += f"Рейтинг: {report['summary']['average_rating']}\n"
            
            send_mail(
                f'📊 Еженедельный отчет EventHub - {timezone.now().strftime("%d.%m.%Y")}',
                plain_message,
                'noreply@eventhub.com',
                [self.organizer.email],
                html_message=html_message,
                fail_silently=True
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending weekly report: {e}")
            return False

class OrganizerTools:
    """Инструменты для организаторов"""
    
    def __init__(self, organizer):
        self.organizer = organizer
    
    def bulk_event_operations(self, event_ids, operation, **kwargs):
        """Массовые операции с мероприятиями"""
        events = self.organizer.organized_events.filter(id__in=event_ids)
        
        if operation == 'activate':
            events.update(is_active=True)
            return f"Активировано {events.count()} мероприятий"
        
        elif operation == 'deactivate':
            events.update(is_active=False)
            return f"Деактивировано {events.count()} мероприятий"
        
        elif operation == 'duplicate':
            duplicated_count = 0
            for event in events:
                new_event = self.duplicate_event(event, **kwargs)
                if new_event:
                    duplicated_count += 1
            return f"Дублировано {duplicated_count} мероприятий"
        
        elif operation == 'send_notification':
            self.bulk_send_notifications(events, **kwargs)
            return f"Уведомления отправлены для {events.count()} мероприятий"
    
    def duplicate_event(self, original_event, new_date=None, new_title=None):
        """Дублирование мероприятия"""
        try:
            new_event = Event.objects.get(pk=original_event.pk)
            new_event.pk = None
            new_event.title = new_title or f"{original_event.title} (Копия)"
            
            if new_date:
                new_event.date = new_date
            else:
                # По умолчанию +7 дней
                new_event.date = original_event.date + timedelta(days=7)
            
            new_event.save()
            
            # Копируем теги
            new_event.tags.set(original_event.tags.all())
            
            return new_event
            
        except Exception as e:
            print(f"Error duplicating event: {e}")
            return None
    
    def bulk_send_notifications(self, events, subject, message):
        """Массовая отправка уведомлений участникам мероприятий"""
        from .notifications_enhanced import enhanced_notification_service
        
        for event in events:
            registrations = event.registrations.all()
            for registration in registrations:
                enhanced_notification_service.send_personalized_notification(
                    user=registration.user,
                    event=event,
                    notification_type='organizer_message',
                    context={
                        'custom_subject': subject,
                        'custom_message': message
                    }
                )
    
    def export_event_data(self, event_ids, format='csv'):
        """Экспорт данных мероприятий"""
        import csv
        from django.http import HttpResponse
        
        events = self.organizer.organized_events.filter(id__in=event_ids)
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="events_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Title', 'Date', 'Location', 'Price', 'Registrations', 'Rating'])
            
            for event in events:
                writer.writerow([
                    event.title,
                    event.date.strftime('%Y-%m-%d %H:%M'),
                    event.location,
                    event.price,
                    event.registrations.count(),
                    event.average_rating
                ])
            
            return response
        
        elif format == 'json':
            # Реализация экспорта в JSON
            pass

# Глобальные утилиты для организаторов
def get_organizer_dashboard(organizer):
    return OrganizerDashboard(organizer)

def get_organizer_tools(organizer):
    return OrganizerTools(organizer)