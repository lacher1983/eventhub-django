from django.db import migrations
from django.utils import timezone
import datetime
from django.conf import settings

def create_sample_events(apps, schema_editor):
    # Используем кастомную модель пользователя
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Event = apps.get_model('events', 'Event')
    Category = apps.get_model('events', 'Category')
    
    # Создаем категорию
    business, created = Category.objects.get_or_create(
        name="Бизнес",
        slug="business",
        defaults={'description': 'Бизнес-мероприятия'}
    )

    # Проверяем, есть ли пользователи
    if User.objects.exists():
        user = User.objects.first()
    else:
        # Создаем тестового пользователя, если нет существующих
        user = User.objects.create(
            username='testuser',
            email='test@example.com',
            is_active=True
        )
        # Устанавливаем пароль
        user.set_password('testpass123')
        user.save()

    # Создаем событие
    Event.objects.create(
        title="Business Forum 2025",
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

class Migration(migrations.Migration):
    dependencies = [
        ('events', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_sample_events),
    ]