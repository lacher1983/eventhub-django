import pytest
from django.utils import timezone
from model_bakery import baker

from events.gamification.core import gamification_engine
from events.models import Event, Registration, Review, Favorite


class GamificationEngineTest:
    def test_award_points(self, test_user):
        initial_points = gamification_engine.get_user_points(test_user)
        
        gamification_engine.award_points(
            test_user, 
            points=10, 
            reason='Test points'
        )
        
        new_points = gamification_engine.get_user_points(test_user)
        assert new_points == initial_points + 10

    def test_level_calculation(self, test_user):
        # Насобирай достаточно очков для повышения уровня
        gamification_engine.award_points(test_user, points=150, reason='Level up')
        
        level = gamification_engine.get_user_level(test_user)
        assert level >= 2

    def test_event_creation_points(self, test_organizer):
        initial_points = gamification_engine.get_user_points(test_organizer)
        
        event = baker.make(
            Event,
            title='Gamification Test Event',
            organizer=test_organizer,
            date=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Активируем сигнал вручную
        from events.signals_gamification import handle_event_creation
        handle_event_creation(Event, event, created=True)
        
        new_points = gamification_engine.get_user_points(test_organizer)
        assert new_points == initial_points + 15  # 15 баллов за создание события

    def test_registration_points(self, test_user, test_event):
        initial_points = gamification_engine.get_user_points(test_user)
        
        registration = Registration.objects.create(
            user=test_user,
            event=test_event
        )
        
        # Активируйте сигнал вручную
        from events.signals_gamification import handle_event_registration
        handle_event_registration(Registration, registration, created=True)
        
        new_points = gamification_engine.get_user_points(test_user)
        assert new_points == initial_points + 5  # 5 points for registration

    def test_review_points(self, test_user, test_event):
        # Первая регистрация на мероприятие
        baker.make(Registration, user=test_user, event=test_event)
        
        initial_points = gamification_engine.get_user_points(test_user)
        
        review = Review.objects.create(
            user=test_user,
            event=test_event,
            rating=5,
            comment='Great event for gamification!'
        )
        
        # активируйте сигнал вручную
        from events.signals_gamification import handle_review_creation
        handle_review_creation(Review, review, created=True)
        
        new_points = gamification_engine.get_user_points(test_user)
        # 3 балла + (5-3) за хороший рейтинг = 5 баллов
        assert new_points == initial_points + 5

    def test_achievement_unlock(self, test_user):
        # Создайте несколько событий для запуска достижений
        for i in range(5):
            gamification_engine.award_points(
                test_user, 
                points=20, 
                reason=f'Test event {i}'
            )
        
        achievements = gamification_engine.get_user_achievements(test_user)
        assert len(achievements) > 0


class GamificationModelsTest:
    def test_user_profile_creation(self, test_user):
        assert hasattr(test_user, 'userprofile')
        assert test_user.userprofile.total_points >= 0

    def test_leaderboard_calculation(self, test_user, test_organizer):
        # Начисляй пользователям различные баллы
        gamification_engine.award_points(test_user, points=50, reason='Test')
        gamification_engine.award_points(test_organizer, points=100, reason='Test')
        
        leaderboard = gamification_engine.get_leaderboard(limit=10)
        assert len(leaderboard) >= 2
        # Организатор должен быть выше из-за большего количества баллов
        assert leaderboard[0]['points'] >= leaderboard[1]['points']