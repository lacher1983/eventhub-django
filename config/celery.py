import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач
app.autodiscover_tasks()

# Расписание для новых задач
app.conf.beat_schedule = {
    # Существующие задачи
    'sync-external-events': {
        'task': 'events.tasks.sync_external_events',
        'schedule': 3600.0,  # Каждый час
    },
    'archive-old-events': {
        'task': 'events.tasks.archive_old_events',
        'schedule': 86400.0,  # Раз в день
    },
    'send-event-reminders': {
        'task': 'events.tasks.send_event_reminders',
        'schedule': crontab(hour=9, minute=0),  # Ежедневно в 9:00
    },
    
    # Новые задачи для организаторов
    'send-weekly-organizer-reports': {
        'task': 'events.tasks_organizers.send_weekly_organizer_reports',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Каждый понедельник в 8:00
    },
    'check-organizer-performance': {
        'task': 'events.tasks_organizers.check_organizer_performance',
        'schedule': crontab(day_of_week=1, hour=10, minute=0),  # Каждый понедельник в 10:00
    },
    'update-organizer-rankings': {
        'task': 'events.tasks_organizers.update_organizer_rankings',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Каждый понедельник в 2:00
    },
    
    # AI и аналитика
    'train-ai-recommendations': {
        'task': 'events.tasks_ai.train_recommendation_models',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Каждое воскресенье в 3:00
    },
    'update-analytics-dashboards': {
        'task': 'events.tasks_analytics.update_all_dashboards',
        'schedule': crontab(hour=4, minute=0),  # Ежедневно в 4:00
    },
}