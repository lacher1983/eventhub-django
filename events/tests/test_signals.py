import pytest
from django.core import mail
from model_bakery import baker

from events.models import Event, Subscription, Notification, EmailConfirmation


class NotificationSignalsTest:
    def test_event_creation_notification(self, test_organizer):
        # Create a subscriber
        subscriber = baker.make('auth.User', email='subscriber@example.com')
        subscription = Subscription.objects.create(user=subscriber)
        subscription.categories.add(test_event.category)
        
        # Create new event
        new_event = baker.make(
            Event,
            title='New Event for Notification',
            organizer=test_organizer,
            category=test_event.category,
            is_active=True
        )
        
        # Check if notification was created
        assert Notification.objects.filter(
            user=subscriber, 
            event=new_event
        ).exists()

    def test_email_confirmation_signal(self, test_user):
        # EmailConfirmation should be created automatically
        assert EmailConfirmation.objects.filter(user=test_user).exists()

    def test_email_sending_on_event_creation(self, test_organizer):
        # Clear outgoing mail
        mail.outbox = []
        
        subscriber = baker.make('auth.User', email='subscriber@example.com')
        subscription = Subscription.objects.create(user=subscriber)
        subscription.categories.add(test_event.category)
        
        # Create new event
        baker.make(
            Event,
            title='Event with Email',
            organizer=test_organizer,
            category=test_event.category,
            is_active=True
        )
        
        # Check if email was sent
        assert len(mail.outbox) == 1
        assert 'Новое мероприятие' in mail.outbox[0].subject