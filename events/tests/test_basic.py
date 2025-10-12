import pytest
from django.test import TestCase
from django.urls import reverse


class BasicDjangoTests(TestCase):
    """Базовые тесты Django"""
    
    def test_home_page(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_login(self):
        """Тест страницы админки"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login


@pytest.mark.django_db
def test_user_creation():
    """Тест создания пользователя"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    assert user.username == 'testuser'
    assert user.check_password('testpass123')
    assert user.email == 'test@example.com'