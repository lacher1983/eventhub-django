from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import matplotlib.pyplot as plt
import io
import base64

def generate_platform_stats():
    """Генерация статистики платформы"""
    from .models import Event, Registration, User
    
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_events': Event.objects.count(),
        'active_events': Event.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'total_registrations': Registration.objects.count(),
        'weekly_registrations': Registration.objects.filter(
            registration_date__gte=week_ago
        ).count(),
        'monthly_registrations': Registration.objects.filter(
            registration_date__gte=month_ago
        ).count(),
    }
    
    # Статистика по категориям
    category_stats = Event.objects.values('category').annotate(
        count=Count('id'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-count')
    
    stats['category_stats'] = list(category_stats)
    
    return stats

def create_events_chart():
    """Создание графика мероприятий"""
    from .models import Event
    
    # Данные для графика
    events_by_month = Event.objects.extra(
        select={'month': "strftime('%%Y-%%m', date)"}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    # Создание графика
    months = [item['month'] for item in events_by_month]
    counts = [item['count'] for item in events_by_month]
    
    plt.figure(figsize=(10, 6))
    plt.plot(months, counts, marker='o', linewidth=2)
    plt.title('Мероприятия по месяцам')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Конвертация в base64 для отображения в HTML
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    
    return f"data:image/png;base64,{graphic}"