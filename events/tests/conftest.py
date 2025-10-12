import os
import django
from django.conf import settings
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker
from rest_framework.test import APIClient

User = get_user_model()

# Настроим Django settings перед импортом любых Django компонентов
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventhub.settings')
    django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker

# Теперь безопасно импортировать DRF
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(client):
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_api_client(api_client):
    user = User.objects.create_user(
        username='apiuser',
        email='api@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_organizer():
    return User.objects.create_user(
        username='organizer',
        email='organizer@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_event(test_organizer):
    from events.models import Event, Category
    category = baker.make(Category, name='Music', slug='music')
    return baker.make(
        Event,
        title='Test Concert',
        organizer=test_organizer,
        category=category,
        is_active=True,
        capacity=100,
        price=1000.00
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(client):
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_api_client(api_client):
    user = User.objects.create_user(
        username='apiuser',
        email='api@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_organizer():
    return User.objects.create_user(
        username='organizer',
        email='organizer@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_event(test_organizer):
    from events.models import Event, Category
    category = baker.make(Category, name='Music', slug='music')
    return baker.make(
        Event,
        title='Test Concert',
        organizer=test_organizer,
        category=category,
        is_active=True,
        capacity=100,
        price=1000.00
    )