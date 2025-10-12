from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GamificationEngine:
    """Движок геймификации для EventHub"""
    
    def __init__(self):
        self.achievements = {}
        self.levels = {}
        self.quests = {}
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных геймификации из базы"""
        try:
            from .models import Achievement, LevelSystem, Quest
            
            self.achievements = {ach.name: ach for ach in Achievement.objects.filter(is_active=True)}
            self.levels = {level.level: level for level in LevelSystem.objects.all()}
            self.quests = {quest.name: quest for quest in Quest.objects.filter(is_active=True)}
            
        except Exception as e:
            logger.error(f"Error loading gamification data: {e}")
            self._create_default_data()
    
    def _create_default_data(self):
        """Создание дефолтных данных геймификации"""
        # Дефолтные достижения
        self.achievements = {
            'first_event': {
                'name': 'Первое мероприятие',
                'description': 'Создайте ваше первое мероприятие',
                'type': 'event',
                'icon': '🎪',
                'points': 10,
                'requirement': {'events_created': 1}
            },
            'social_butterfly': {
                'name': 'Социальная бабочка',
                'description': 'Зарегистрируйтесь на 10 мероприятий',
                'type': 'social',
                'icon': '🦋',
                'points': 25,
                'requirement': {'events_attended': 10}
            },
            'explorer': {
                'name': 'Исследователь',
                'description': 'Посетите мероприятия 5 разных категорий',
                'type': 'exploration',
                'icon': '🧭',
                'points': 30,
                'requirement': {'categories_explored': 5}
            },
            'reviewer': {
                'name': 'Критик',
                'description': 'Напишите 5 отзывов о мероприятиях',
                'type': 'mastery',
                'icon': '📝',
                'points': 20,
                'requirement': {'reviews_written': 5}
            },
            'streak_master': {
                'name': 'Мастер серии',
                'description': 'Будьте активны 7 дней подряд',
                'type': 'special',
                'icon': '🔥',
                'points': 50,
                'requirement': {'streak_days': 7}
            }
        }
        
        # Дефолтные уровни
        self.levels = {
            1: {'name': 'Новичок', 'min_points': 0, 'max_points': 50, 'icon': '🌱', 'color': '#95a5a6'},
            2: {'name': 'Энтузиаст', 'min_points': 51, 'max_points': 150, 'icon': '⭐', 'color': '#3498db'},
            3: {'name': 'Знаток', 'min_points': 151, 'max_points': 300, 'icon': '🏅', 'color': '#9b59b6'},
            4: {'name': 'Эксперт', 'min_points': 301, 'max_points': 500, 'icon': '👑', 'color': '#e74c3c'},
            5: {'name': 'Легенда', 'min_points': 501, 'max_points': 1000, 'icon': '💫', 'color': '#f1c40f'}
        }
    
    @transaction.atomic
    def handle_user_action(self, user, action_type: str, **kwargs):
        """Обработка действий пользователя"""
        try:
            # Обновляем профиль пользователя
            profile = self._get_or_create_user_profile(user)
            profile.update_stats()
            
            # Обновляем streak
            self._update_streak(profile)
            
            # Проверяем достижения
            unlocked_achievements = self._check_achievements(profile)
            
            # Проверяем задания
            completed_quests = self._check_quests(profile, action_type, kwargs)
            
            # Обновляем уровень
            new_level = self._update_level(profile)
            
            # Обновляем таблицу лидеров
            self._update_leaderboard(user, profile.total_points)
            
            return {
                'unlocked_achievements': unlocked_achievements,
                'completed_quests': completed_quests,
                'level_up': new_level is not None,
                'new_level': new_level,
                'points_added': kwargs.get('points', 0)
            }
            
        except Exception as e:
            logger.error(f"Error handling user action: {e}")
            return {}
    
    def _get_or_create_user_profile(self, user):
        """Получение или создание игрового профиля"""
        from .models import UserProfile, LevelSystem
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if created or not profile.current_level:
            # Устанавливаем начальный уровень
            first_level = LevelSystem.objects.filter(level=1).first()
            if first_level:
                profile.current_level = first_level
                profile.save()
        
        return profile
    
    def _update_streak(self, profile):
        """Обновление серии активных дней"""
        from datetime import timedelta
        
        now = timezone.now()
        last_activity = profile.last_activity
        
        if last_activity.date() == now.date():
            # Уже обновляли сегодня
            return
        
        if last_activity.date() == (now - timedelta(days=1)).date():
            # Подряд идут дни
            profile.streak_days += 1
        else:
            # Сброс серии
            profile.streak_days = 1
        
        profile.last_activity = now
        profile.save()
    
    def _check_achievements(self, profile):
        """Проверка достижений пользователя"""
        from .models import Achievement, UserAchievement
        
        unlocked = []
        
        for achievement_name, achievement_data in self.achievements.items():
            if isinstance(achievement_data, dict):
                # Используем дефолтные данные
                requirement = achievement_data['requirement']
                points = achievement_data['points']
            else:
                # Используем данные из базы
                requirement = achievement_data.requirement
                points = achievement_data.points
            
            # Проверяем выполнение требований
            if self._check_requirement(profile, requirement):
                # Создаем или обновляем достижение
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=profile.user,
                    achievement=achievement_data if not isinstance(achievement_data, dict) else None,
                    defaults={
                        'is_unlocked': True,
                        'progress': 1.0
                    }
                )
                
                if created or not user_achievement.is_unlocked:
                    user_achievement.is_unlocked = True
                    user_achievement.progress = 1.0
                    user_achievement.save()
                    
                    # Добавляем очки
                    profile.total_points += points
                    profile.save()
                    
                    unlocked.append({
                        'name': achievement_data['name'] if isinstance(achievement_data, dict) else achievement_data.name,
                        'icon': achievement_data['icon'] if isinstance(achievement_data, dict) else achievement_data.icon,
                        'points': points,
                        'description': achievement_data['description'] if isinstance(achievement_data, dict) else achievement_data.description
                    })
        
        return unlocked
    
    def _check_requirement(self, profile, requirement: Dict) -> bool:
        """Проверка выполнения требования"""
        stats = profile.stats
        
        for key, required_value in requirement.items():
            current_value = stats.get(key, 0)
            
            if key == 'streak_days':
                current_value = profile.streak_days
            
            if current_value < required_value:
                return False
        
        return True
    
    def _check_quests(self, profile, action_type: str, action_data: Dict):
        """Проверка выполнения заданий"""
        from .models import UserQuest, Quest
        
        completed = []
        
        # Получаем активные задания пользователя
        user_quests = UserQuest.objects.filter(
            user=profile.user,
            quest__is_active=True,
            is_completed=False
        )
        
        for user_quest in user_quests:
            quest = user_quest.quest
            requirement = quest.requirement
            
            # Проверяем соответствует ли действие типу задания
            if requirement.get('action_type') != action_type:
                continue
            
            # Обновляем прогресс
            progress = self._calculate_quest_progress(user_quest, action_data)
            user_quest.progress = progress
            
            if progress >= 1.0 and not user_quest.is_completed:
                user_quest.is_completed = True
                user_quest.completed_at = timezone.now()
                user_quest.save()
                
                # Награждаем пользователя
                profile.total_points += quest.points_reward
                profile.save()
                
                completed.append({
                    'name': quest.name,
                    'points': quest.points_reward,
                    'description': quest.description
                })
            else:
                user_quest.save()
        
        return completed
    
    def _calculate_quest_progress(self, user_quest, action_data: Dict) -> float:
        """Расчет прогресса выполнения задания"""
        quest = user_quest.quest
        requirement = quest.requirement
        
        if 'target_count' in requirement:
            current_count = user_quest.progress * requirement['target_count']
            current_count += action_data.get('count', 1)
            return min(current_count / requirement['target_count'], 1.0)
        
        return 1.0  # По умолчанию считаем выполненным
    
    def _update_level(self, profile):
        """Обновление уровня пользователя"""
        from .models import LevelSystem
        
        current_level = profile.current_level
        total_points = profile.total_points
        
        # Находим подходящий уровень
        new_level = LevelSystem.objects.filter(
            min_points__lte=total_points,
            max_points__gte=total_points
        ).first()
        
        if new_level and (not current_level or current_level.level != new_level.level):
            profile.current_level = new_level
            profile.save()
            return new_level
        
        return None
    
    def _update_leaderboard(self, user, points):
        """Обновление таблицы лидеров"""
        from .models import Leaderboard
        
        try:
            # Получаем или создаем позицию пользователя
            leaderboard_entry, created = Leaderboard.objects.get_or_create(
                user=user,
                defaults={'points': points, 'position': 0}
            )
            
            if not created:
                leaderboard_entry.points = points
                leaderboard_entry.save()
            
            # Пересчитываем позиции всех пользователей
            self._recalculate_leaderboard_positions()
            
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")
    
    def _recalculate_leaderboard_positions(self):
        """Пересчет позиций в таблице лидеров"""
        from .models import Leaderboard
        
        # Получаем все записи отсортированные по очкам
        entries = Leaderboard.objects.all().order_by('-points')
        
        with transaction.atomic():
            for position, entry in enumerate(entries, start=1):
                entry.position = position
                entry.save()
    
    def get_user_progress(self, user):
        """Получение прогресса пользователя"""
        from .models import UserProfile, UserAchievement, UserQuest
        
        profile = self._get_or_create_user_profile(user)
        profile.update_stats()
        
        achievements = UserAchievement.objects.filter(user=user)
        quests = UserQuest.objects.filter(user=user, quest__is_active=True)
        
        # Следующий уровень
        next_level = None
        if profile.current_level:
            next_level = LevelSystem.objects.filter(
                level=profile.current_level.level + 1
            ).first()
        
        # Прогресс до следующего уровня
        level_progress = 0
        if profile.current_level and next_level:
            current_range = profile.current_level.max_points - profile.current_level.min_points
            user_progress = profile.total_points - profile.current_level.min_points
            level_progress = min(user_progress / current_range, 1.0) if current_range > 0 else 1.0
        
        return {
            'profile': profile,
            'level': profile.current_level,
            'next_level': next_level,
            'level_progress': level_progress,
            'achievements': achievements,
            'active_quests': quests.filter(is_completed=False),
            'completed_quests': quests.filter(is_completed=True),
            'leaderboard_position': self._get_leaderboard_position(user),
            'stats': profile.stats
        }
    
    def _get_leaderboard_position(self, user):
        """Получение позиции пользователя в таблице лидеров"""
        from .models import Leaderboard
        
        try:
            entry = Leaderboard.objects.get(user=user)
            return entry.position
        except Leaderboard.DoesNotExist:
            return None
    
    def award_points(self, user, points: int, reason: str):
        """Начисление очков пользователю"""
        try:
            profile = self._get_or_create_user_profile(user)
            profile.total_points += points
            profile.save()
            
            # Логируем начисление очков
            logger.info(f"Awarded {points} points to {user.username} for: {reason}")
            
            # Проверяем достижения и уровень
            self.handle_user_action(user, 'points_awarded', points=points)
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            return False
    
    def create_daily_quests(self):
        """Создание ежедневных заданий"""
        from .models import Quest
        from datetime import datetime, timedelta
        
        daily_quests = [
            {
                'name': 'Первое мероприятие дня',
                'description': 'Зарегистрируйтесь на одно мероприятие сегодня',
                'quest_type': 'daily',
                'points_reward': 5,
                'requirement': {
                    'action_type': 'event_registration',
                    'target_count': 1
                }
            },
            {
                'name': 'Активный исследователь',
                'description': 'Посетите мероприятия из 2 разных категорий',
                'quest_type': 'daily',
                'points_reward': 10,
                'requirement': {
                    'action_type': 'category_exploration',
                    'target_count': 2
                }
            },
            {
                'name': 'Социальная активность',
                'description': 'Добавьте 3 мероприятия в избранное',
                'quest_type': 'daily',
                'points_reward': 8,
                'requirement': {
                    'action_type': 'add_favorite',
                    'target_count': 3
                }
            }
        ]
        
        tomorrow = timezone.now() + timedelta(days=1)
        
        for quest_data in daily_quests:
            Quest.objects.get_or_create(
                name=quest_data['name'],
                defaults={
                    'description': quest_data['description'],
                    'quest_type': quest_data['quest_type'],
                    'points_reward': quest_data['points_reward'],
                    'requirement': quest_data['requirement'],
                    'expires_at': tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                }
            )

# Глобальный экземпляр движка геймификации
gamification_engine = GamificationEngine()