from celery import shared_task
from django.core.management import call_command
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Event, Registration
from .models import User
from .organizer_dashboard import get_organizer_dashboard


@shared_task
def send_event_reminders():
    """Отправка напоминаний о мероприятиях"""
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    events = Event.objects.filter(
        date__date=tomorrow.date(), 
        is_active=True)
    
    for event in events:
        registrations = event.registrations.all()
        for registration in registrations:
            send_mail(
                f'Напоминание: {event.title}',
                f'''Привет, {registration.user.username}!

Напоминаем, что завтра состоится мероприятие "{event.title}".
📅 Дата: {event.date.strftime('%d.%m.%Y в %H:%M')}
📍 Место: {event.location}

Не пропустите!''',
                'noreply@eventhub.com',
                [registration.user.email],
                fail_silently=True,
            )


@shared_task
def sync_external_events():
    """Синхронизация внешних мероприятий"""    
    call_command('sync_external_events')

@shared_task  
def archive_old_events():
    """Архивация старых мероприятий"""
    call_command('sync_external_events', '--archive-old')


@shared_task
def reset_daily_quests():
    """Сброс и создание ежедневных заданий"""
    from .gamification.core import gamification_engine
    from .models import Quest, UserQuest
    
    # Удаляем старые ежедневные задания
    Quest.objects.filter(quest_type='daily').delete()
    
    # Создаем новые ежедневные задания
    gamification_engine.create_daily_quests()
    
    print("Daily quests reset successfully")

@shared_task
def update_leaderboard():
    """Обновление таблицы лидеров"""
    from .gamification.core import gamification_engine
    from .models import UserProfile
    
    # Обновляем статистику всех пользователей
    profiles = UserProfile.objects.all()
    for profile in profiles:
        profile.update_stats()
    
    print("Leaderboard updated successfully")

@shared_task
def award_streak_bonus():
    """Начисление бонусов за серии"""
    from .models import UserProfile
    from .gamification.core import gamification_engine
    
    profiles = UserProfile.objects.filter(streak_days__gt=0)
    
    for profile in profiles:
        # Награждаем за серию
        if profile.streak_days >= 7:
            gamification_engine.award_points(
                profile.user,
                points=25,
                reason=f"Бонус за серию из {profile.streak_days} дней"
            )
        elif profile.streak_days >= 30:
            gamification_engine.award_points(
                profile.user,
                points=100,
                reason=f"Бонус за серию из {profile.streak_days} дней"
            )
    
    print("Streak bonuses awarded")

@shared_task
def check_achievement_progress():
    """Проверка прогресса достижений"""
    from django.contrib.auth import get_user_model
    from .gamification.core import gamification_engine
    
    User = get_user_model()
    users = User.objects.all()
    
    for user in users:
        gamification_engine.handle_user_action(user, 'progress_check')
    
    print("Achievement progress checked for all users")


@shared_task
def send_weekly_organizer_reports():
    """Еженедельная отправка отчетов всем организаторам"""
    organizers = User.objects.filter(role='organizer')
    
    for organizer in organizers:
        try:
            dashboard = get_organizer_dashboard(organizer)
            success = dashboard.send_weekly_report()
            
            if success:
                print(f"Weekly report sent to {organizer.email}")
            else:
                print(f"Failed to send weekly report to {organizer.email}")
                
        except Exception as e:
            print(f"Error sending report to {organizer.email}: {e}")
            continue

@shared_task
def check_organizer_performance():
    """Проверка производительности организаторов и отправка предупреждений"""
    from datetime import timedelta
    
    organizers = User.objects.filter(role='organizer')
    warning_threshold = timezone.now() - timedelta(days=30)
    
    for organizer in organizers:
        try:
            # Проверяем активность за последние 30 дней
            recent_events = organizer.organized_events.filter(
                created_at__gte=warning_threshold
            )
            
            if recent_events.count() == 0:
                # Отправляем предупреждение о неактивности
                send_mail(
                    '⚠️ Ваш аккаунт организатора неактивен',
                    f'''Привет, {organizer.username}!

Мы заметили, что вы не создавали мероприятий в течение последних 30 дней. 
Не забывайте, что активные организаторы получают больше внимания от участников!

Создайте новое мероприятие сегодня: http://127.0.0.1:8000/event/new/

С уважением,
Команда EventHub''',
                    'noreply@eventhub.com',
                    [organizer.email],
                    fail_silently=True
                )
                
        except Exception as e:
            print(f"Error checking performance for {organizer.username}: {e}")

@shared_task
def update_organizer_rankings():
    """Обновление рейтингов и рангов организаторов"""
    organizers = User.objects.filter(role='organizer')
    
    for organizer in organizers:
        try:
            dashboard = get_organizer_dashboard(organizer)
            stats = dashboard.get_dashboard_stats(90)  # За 3 месяца
            
            # Расчет ранга на основе метрик
            rank_score = (
                stats['total_events'] * 10 +
                stats['total_registrations'] * 5 +
                stats['avg_rating'] * 20 +
                stats['engagement_metrics']['engagement_score']
            )
            
            # Сохраняем ранг в профиле (если есть поле)
            if hasattr(organizer, 'organizer_rank'):
                organizer.organizer_rank = rank_score
                organizer.save()
                
        except Exception as e:
            print(f"Error updating rank for {organizer.username}: {e}")

@shared_task
def send_weekly_report():
    for organizer in User.objects.filter(role='organizer'):
        # генерация отчёта
        send_mail(...)