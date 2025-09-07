from django.core.management.base import BaseCommand
from events.models import Event, Category
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample events for testing'
    
    def handle(self, *args, **options):
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found!'))
            return
            
        # Создаем категорию
        health, _ = Category.objects.get_or_create(
            name="Здоровье",
            slug="health",
            defaults={'description': 'Мероприятия о здоровье'}
        )
        
        # Событие 7: Йога-марафон
        event = Event.objects.create(
            title="Йога Марафон",
            short_description="24-часовой марафон йоги",
            description="Непрерывные занятия йогой в течение 24 часов",
            date=timezone.now() + datetime.timedelta(days=14),
            location="Онлайн",
            event_type="online",
            category=health,
            organizer=user,
            price=0,
            capacity=1000
        )
        
        self.stdout.write(self.style.SUCCESS(f'Created event: {event.title}'))