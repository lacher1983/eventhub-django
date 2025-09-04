from django.db import migrations
from django.conf import settings
from django.utils import timezone
import datetime

def create_sample_events(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Category = apps.get_model('events', 'Category')
    Event = apps.get_model('events', 'Event')

    # Создаем категорию
    business, _ = Category.objects.get_or_create(
        name="Бизнес",
        slug="business",
        defaults={'description': 'Бизнес-мероприятия'}
    )
    
    # Получаем первого пользователя
    user = User.objects.first()
    
    if user:
        # Событие 6: Бизнес-форум
        Event.objects.create(
            title="Business Forum 2024",
            short_description="Международный бизнес-форум",
            description="Встреча с ведущими предпринимателями и инвесторами",
            date=timezone.now() + datetime.timedelta(days=90),
            location="Сколково",
            event_type="hybrid",
            category=business,
            organizer=user,
            price=10000,
            capacity=500
        )
    if not user:
        # Если нет пользователей, создаем или пропускаем
        return
    

def reverse_events(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Event.objects.filter(title="Business Forum 2024").delete()

class Migration(migrations.Migration):
    dependencies = [
        ('events', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_sample_events),
    ]