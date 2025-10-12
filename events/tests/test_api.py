import pytest
from rest_framework import status
from model_bakery import baker


class EventAPITestCase(APITestCase):
    def test_event_list_api(self, api_client, test_event):
        response = api_client.get('/api/events/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_event_detail_api(self, api_client, test_event):
        response = api_client.get(f'/api/events/{test_event.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == test_event.title

    def test_event_create_api_requires_auth(self, api_client):
        response = api_client.post('/api/events/', {
            'title': 'New Event',
            'date': '2024-12-31T20:00:00Z',
            'capacity': 100
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_event_create_api_authenticated(self, authenticated_api_client):
        response = authenticated_api_client.post('/api/events/', {
            'title': 'API Created Event',
            'date': '2024-12-31T20:00:00Z',
            'capacity': 50,
            'price': 1000.00
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'API Created Event'


class RegistrationAPITest(APITestCase):
    def test_register_via_api(self, authenticated_api_client, test_event):
        response = authenticated_api_client.post(
            f'/api/events/{test_event.pk}/register/'
        )
        assert response.status_code == status.HTTP_201_CREATED


class ReviewAPITest(APITestCase):
    def test_review_create_api(self, authenticated_api_client, test_event):
        # First register for the event
        baker.make(
            'events.Registration',
            user=authenticated_api_client.user,
            event=test_event
        )
        
        response = authenticated_api_client.post(
            f'/api/events/{test_event.pk}/reviews/',
            {
                'rating': 5,
                'comment': 'Great event via API!'
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 5


class UserAPITest(APITestCase):
    def test_user_profile_api(self, authenticated_api_client):
        response = authenticated_api_client.get('/api/users/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert 'username' in response.data

    def test_user_update_profile_api(self, authenticated_api_client):
        response = authenticated_api_client.patch(
            '/api/users/profile/',
            {'bio': 'Updated bio via API'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Updated bio via API'