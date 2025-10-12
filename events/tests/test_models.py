from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from ..models import Event, Category, Registration, Favorite, Review, UserProfile
from django.core.exceptions import ValidationError
from model_bakery import baker

User = get_user_model()

class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Технологии',
            slug='technology',
            description='Технологические мероприятия'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            category=self.category,
            organizer=self.user,
            price=1000,
            capacity=100
        )

    def test_event_creation(self):
        """Тест создания мероприятия"""
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.organizer, self.user)
        self.assertTrue(self.event.is_active)
        self.assertEqual(self.event.get_absolute_url(), f'/event/{self.event.pk}/')

    def test_event_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.event), 'Test Event')

    def test_free_event_detection(self):
        """Тест определения бесплатного мероприятия"""
        free_event = Event.objects.create(
            title='Free Event',
            description='Free Event Description',
            date=timezone.now() + timedelta(days=1),
            location='Online',
            category=self.category,
            organizer=self.user,
            price=0,
            capacity=1000
        )
        self.assertTrue(free_event.is_free_event)

    def test_ticket_availability(self):
        """Тест доступности билетов"""
        self.assertTrue(self.event.is_ticket_available())
        self.assertTrue(self.event.is_ticket_available(5))

    def test_event_badges(self):
        """Тест системы бейджей"""
        badges = self.event.get_active_badges()
        self.assertIsInstance(badges, list)

class RegistrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', slug='test')
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            category=self.category,
            organizer=self.user
        )

    def test_registration_creation(self):
        """Тест создания регистрации"""
        registration = Registration.objects.create(
            user=self.user,
            event=self.event
        )
        self.assertEqual(registration.user, self.user)
        self.assertEqual(registration.event, self.event)
        self.assertEqual(registration.status, 'pending')

    def test_unique_registration(self):
        """Тест уникальности регистрации"""
        Registration.objects.create(user=self.user, event=self.event)
        # Попытка создать дубликат
        with self.assertRaises(Exception):
            Registration.objects.create(user=self.user, event=self.event)


class ReviewModelTest(TestCase):
    def test_review_creation(self, test_user, test_event):
        review = Review.objects.create(
            user=test_user,
            event=test_event,
            rating=5,
            comment='Great event!'
        )
        assert review.rating == 5
        assert review.comment == 'Great event!'

    def test_rating_validation(self, test_user, test_event):
        # Valid rating
        review = Review(user=test_user, event=test_event, rating=5)
        review.full_clean()  # Should not raise
        
        # Invalid rating
        review.rating = 6
        with pytest.raises(ValidationError):
            review.full_clean()


class UserProfileModelTest(TestCase):
    def test_profile_creation(self, test_user):
        profile = UserProfile.objects.create(
            user=test_user,
            bio='Test bio',
            avatar='avatars/test.jpg'
        )
        assert profile.user == test_user
        assert profile.bio == 'Test bio'

    def test_profile_auto_creation(self, test_user):
        # Profile should be created automatically via signal
        assert hasattr(test_user, 'userprofile')
        assert test_user.userprofile is not None