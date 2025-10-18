from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Event, Category
from model_bakery import baker

User = get_user_model()

class EventViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Технологии',
            slug='technology'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date='2025-12-31 23:59:00+00:00',
            location='Test Location',
            category=self.category,
            organizer=self.user,
            price=1000,
            capacity=100
        )

    def test_event_list_view(self):
        """Тест списка мероприятий"""
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_list.html')
        self.assertContains(response, 'Test Event')

    def test_event_detail_view(self):
        """Тест детальной страницы мероприятия"""
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')
        self.assertContains(response, self.event.title)

    def test_event_create_view_requires_login(self):
        """Тест что создание мероприятия требует авторизации"""
        response = self.client.get(reverse('event_create'))
        self.assertNotEqual(response.status_code, 200)  # Должен редирект на логин

    def test_event_create_view_authenticated(self):
        """Тест создания мероприятия авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 200)

    def test_event_search_view(self, client):
        response = client.get(reverse('event_search') + '?q=concert')
        assert response.status_code == 200

    def test_event_filtering(self, client, test_event):
        # Фильтр категории теста
        response = client.get(
            reverse('event_list') + f'?category={test_event.category.slug}'
        )
        assert response.status_code == 200
        assert len(response.context['events']) >= 1

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        self.category = Category.objects.create(name='API Category', slug='api')
        self.event = Event.objects.create(
            title='API Test Event',
            description='API Test Description',
            date='2025-12-31 23:59:00+00:00',
            location='API Location',
            category=self.category,
            organizer=self.user
        )

    def test_events_api(self):
        """Тест API мероприятий"""
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_api(self):
        """Тест детального API мероприятия"""
        response = self.client.get(f'/api/events/{self.event.id}/')
        self.assertEqual(response.status_code, 200)

class RegistrationViewsTest(TestCase):
    def test_register_for_event(self, authenticated_client, test_event):
        response = authenticated_client.post(
            reverse('register_for_event', args=[test_event.pk])
        )
        assert response.status_code == 302  # Redirect
        assert test_event.registrations.filter(
            user=authenticated_client.user
        ).exists()

    def test_user_registrations_view(self, authenticated_client):
        response = authenticated_client.get(reverse('user_registrations'))
        assert response.status_code == 200


class FavoriteViewsTest(TestCase):
    def test_toggle_favorite(self, authenticated_api_client, test_event):
        response = authenticated_api_client.post(
            reverse('toggle_favorite', args=[test_event.pk])
        )
        assert response.status_code == 200
        assert response.json()['status'] in ['added', 'removed']

    def test_favorite_list_view(self, authenticated_client):
        response = authenticated_client.get(reverse('favorite_list'))
        assert response.status_code == 200


class ReviewViewsTest(TestCase):
    def test_add_review_requires_registration(
        self, authenticated_client, test_event
    ):
        response = authenticated_client.get(
            reverse('add_review', args=[test_event.pk])
        )
        # Необходимо перенаправить, поскольку пользователь не зарегистрирован
        assert response.status_code == 302