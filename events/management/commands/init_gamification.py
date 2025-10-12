from django.core.management.base import BaseCommand
from events.models import Achievement, LevelSystem, Quest
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Initialize gamification system with default data'
    
    def handle(self, *args, **options):
        self.stdout.write('🎮 Initializing gamification system...')
        
        # Создаем уровни
        levels_data = [
            {'level': 1, 'level_name': 'Новичок', 'min_points': 0, 'max_points': 50, 'badge_icon': '🌱', 'color': '#95a5a6'},
            {'level': 2, 'level_name': 'Энтузиаст', 'min_points': 51, 'max_points': 150, 'badge_icon': '⭐', 'color': '#3498db'},
            {'level': 3, 'level_name': 'Знаток', 'min_points': 151, 'max_points': 300, 'badge_icon': '🏅', 'color': '#9b59b6'},
            {'level': 4, 'level_name': 'Эксперт', 'min_points': 301, 'max_points': 500, 'badge_icon': '👑', 'color': '#e74c3c'},
            {'level': 5, 'level_name': 'Легенда', 'min_points': 501, 'max_points': 1000, 'badge_icon': '💫', 'color': '#f1c40f'},
        ]
        
        for level_data in levels_data:
            LevelSystem.objects.get_or_create(
                level=level_data['level'],
                defaults=level_data
            )
        
        # Создаем достижения
        achievements_data = [
            {
                'name': 'Первое мероприятие',
                'description': 'Создайте ваше первое мероприятие',
                'achievement_type': 'event',
                'icon': '🎪',
                'points': 10,
                'requirement': {'events_created': 1}
            },
            {
                'name': 'Социальная бабочка',
                'description': 'Зарегистрируйтесь на 10 мероприятий',
                'achievement_type': 'social',
                'icon': '🦋',
                'points': 25,
                'requirement': {'events_attended': 10}
            },
            {
                'name': 'Исследователь',
                'description': 'Посетите мероприятия 5 разных категорий',
                'achievement_type': 'exploration',
                'icon': '🧭',
                'points': 30,
                'requirement': {'categories_explored': 5}
            },
            {
                'name': 'Критик',
                'description': 'Напишите 5 отзывов о мероприятиях',
                'achievement_type': 'mastery',
                'icon': '📝',
                'points': 20,
                'requirement': {'reviews_written': 5}
            },
            {
                'name': 'Мастер серии',
                'description': 'Будьте активны 7 дней подряд',
                'achievement_type': 'special',
                'icon': '🔥',
                'points': 50,
                'requirement': {'streak_days': 7}
            },
            {
                'name': 'Организатор',
                'description': 'Создайте 5 мероприятий',
                'achievement_type': 'event',
                'icon': '🎯',
                'points': 40,
                'requirement': {'events_created': 5}
            },
            {
                'name': 'Ветеран',
                'description': 'Посетите 25 мероприятий',
                'achievement_type': 'social',
                'icon': '🎖️',
                'points': 75,
                'requirement': {'events_attended': 25}
            }
        ]
        
        for ach_data in achievements_data:
            Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
        
        # Создаем ежедневные задания
        tomorrow = timezone.now() + timedelta(days=1)
        daily_quests = [
            {
                'name': 'Первое мероприятие дня',
                'description': 'Зарегистрируйтесь на одно мероприятие сегодня',
                'quest_type': 'daily',
                'points_reward': 5,
                'requirement': {'action_type': 'event_registration', 'target_count': 1},
                'expires_at': tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            },
            {
                'name': 'Активный исследователь',
                'description': 'Посетите мероприятия из 2 разных категорий',
                'quest_type': 'daily',
                'points_reward': 10,
                'requirement': {'action_type': 'category_exploration', 'target_count': 2},
                'expires_at': tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            }
        ]
        
        for quest_data in daily_quests:
            Quest.objects.get_or_create(
                name=quest_data['name'],
                quest_type='daily',
                defaults=quest_data
            )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Gamification system initialized successfully!')
        )