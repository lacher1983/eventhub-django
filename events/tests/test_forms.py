import pytest
from django.utils import timezone

from events.forms import EventForm, RegistrationForm, ReviewForm, CustomUserCreationForm


class EventFormTest:
    def test_valid_event_form(self, test_organizer):
        form_data = {
            'title': 'Test Event Form',
            'description': 'Test description',
            'date': timezone.now() + timezone.timedelta(days=7),
            'location': 'Test Location',
            'capacity': 100,
            'price': 1000.00,
            'category': test_event.category.id
        }
        form = EventForm(data=form_data)
        assert form.is_valid()

    def test_event_form_past_date(self):
        form_data = {
            'title': 'Past Event',
            'date': timezone.now() - timezone.timedelta(days=1),
            'capacity': 100
        }
        form = EventForm(data=form_data)
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_event_form_negative_capacity(self):
        form_data = {
            'title': 'Invalid Capacity Event',
            'date': timezone.now() + timezone.timedelta(days=7),
            'capacity': -10
        }
        form = EventForm(data=form_data)
        assert not form.is_valid()
        assert 'capacity' in form.errors


class UserCreationFormTest:
    def test_valid_user_creation_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()

    def test_password_mismatch(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
        }
        form = CustomUserCreationForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors