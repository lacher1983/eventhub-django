from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Event, Category, Registration

User = get_user_model()

class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testorganizer', 
            password='testpass',
            role='organizer'
        )
        self.category = Category.objects.create(name="Test Category")
        
    def test_event_creation(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            date=timezone.now() + timedelta(days=7),
            location="Test Location",
            event_type="offline",
            category=self.category,
            organizer=self.user,
            price=1000,
            capacity=100
        )
        self.assertEqual(event.title, "Test Event")
        self.assertTrue(event.is_active)