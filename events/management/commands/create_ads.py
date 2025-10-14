from django.core.management.base import BaseCommand
from events.models import Event, Category, Advertisement
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые мероприятия и рекламные баннеры'

    def handle(self, *args, **options):
        # Удаляем старые тестовые баннеры
        Advertisement.objects.filter(title__contains="Скидка").delete()
        Advertisement.objects.filter(title__contains="Главное событие").delete()
        Advertisement.objects.filter(title__contains="Премиум").delete()
        Advertisement.objects.filter(title__contains="Не пропустите").delete()

        # Создаем категории если их нет
        self.create_categories()
        
        # Получаем или создаем пользователя
        user = self.get_or_create_organizer()
        
        # Создаем рекламные баннеры
        self.create_advertisements()
        
        # Создаем тестовые мероприятия
        self.create_sample_events(user)

    def create_categories(self):
        """Создает категории мероприятий если они не существуют"""
        categories = {
            'concert': '🎵 Концерты',
            'conference': '💼 Конференции', 
            'workshop': '🔧 Мастер-классы',
            'sport': '⚽ Спорт',
            'exhibition': '🖼️ Выставки'
        }
        
        for slug, name in categories.items():
            category, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создана категория: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ Категория уже существует: {name}'))

    def get_or_create_organizer(self):
        """Создает или получает пользователя-организатора"""
        user, created = User.objects.get_or_create(
            username='organizer',
            defaults={
                'email': 'organizer@example.com',
                'first_name': 'Организатор',
                'last_name': 'Тестовый'
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS('✅ Создан пользователь-организатор'))
        else:
            self.stdout.write(self.style.WARNING('ℹ Пользователь-организатор уже существует'))
        
        return user

    def create_advertisements(self):
        """Создает рекламные баннеры"""
        ads_data = [
            {
                'title': 'Скидка 20% на все мероприятия!',
                'ad_type': 'banner',
                'position': 'top',
                'content': 'Успейте забронировать! Ограниченное предложение до конца месяца',
                'link': '/events/?promo=20percent',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'is_active': True,
                'background_color': '#ff6b6b',
                'text_color': '#ffffff'
            },
            {
                'title': 'Главное событие месяца',
                'ad_type': 'video', 
                'position': 'sidebar',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'link': '/events/featured/',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=60),
                'is_active': True,
                'background_color': '#4ecdc4',
                'text_color': '#ffffff'
            },
            {
                'title': 'Премиум-мероприятия со скидкой',
                'ad_type': 'banner',
                'position': 'between_events',
                'content': 'Только этой недели скидки на премиум-мероприятия',
                'link': '/events/premium/',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True,
                'background_color': '#45b7d1',
                'text_color': '#ffffff'
            },
            {
                'title': 'Не пропустите лучшие события',
                'ad_type': 'banner', 
                'position': 'bottom',
                'content': 'Подпишитесь на рассылку и получайте уведомления',
                'link': '/newsletter/',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=90),
                'is_active': True,
                'background_color': '#96ceb4',
                'text_color': '#ffffff'
            }
        ]
        
        created_count = 0
        for ad_data in ads_data:
            ad, created = Advertisement.objects.get_or_create(
                title=ad_data['title'],
                defaults=ad_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создан баннер: {ad.title}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'ℹ Баннер уже существует: {ad.title}'))
        
        if created_count == 0:
            self.stdout.write(self.style.WARNING('ℹ Новые баннеры не созданы (возможно уже существуют)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Создано {created_count} баннеров!'))

    def create_sample_events(self, user):
        """Создает тестовые мероприятия"""
        # Тестовые мероприятия в Москве
        sample_events = [
            {
                'title': 'Концерт классической музыки',
                'description': 'Прекрасный вечер классической музыки в историческом зале. Приглашаем всех ценителей искусства.',
                'location': 'Москва, ул. Тверская, 13',
                'latitude': 55.7602,
                'longitude': 37.6085,
                'price': 1500,
                'category_name': '🎵 Концерты',
                'max_participants': 200
            },
            {
                'title': 'IT конференция 2024',
                'description': 'Крупнейшая IT конференция года с ведущими экспертами индустрии. Новые технологии и тренды.',
                'location': 'Москва, Красная площадь, 1',
                'latitude': 55.7539,
                'longitude': 37.6208,
                'price': 0,
                'category_name': '💼 Конференции',
                'max_participants': 500
            },
            {
                'title': 'Мастер-класс по кулинарии',
                'description': 'Научим готовить итальянскую пасту от шеф-повара. Все ингредиенты включены в стоимость.',
                'location': 'Москва, Арбат, 25',
                'latitude': 55.7495,
                'longitude': 37.5908,
                'price': 2500,
                'category_name': '🔧 Мастер-классы',
                'max_participants': 20
            },
            {
                'title': 'Футбольный матч',
                'description': 'Товарищеский матч между командами. Приходите поболеть за любимых игроков!',
                'location': 'Москва, Лужники',
                'latitude': 55.7157,
                'longitude': 37.5536,
                'price': 500,
                'category_name': '⚽ Спорт',
                'max_participants': 5000
            },
            {
                'title': 'Выставка современного искусства',
                'description': 'Работы современных художников со всего мира. Уникальная коллекция картин и инсталляций.',
                'location': 'Москва, Крымский вал, 10',
                'latitude': 55.7358,
                'longitude': 37.6056,
                'price': 300,
                'category_name': '🖼️ Выставки',
                'max_participants': 100
            },
            {
                'title': 'Воркшоп по программированию',
                'description': 'Практический воркшоп по современным фреймворкам. Подходит для начинающих и опытных разработчиков.',
                'location': 'Москва, Пресненская набережная, 8',
                'latitude': 55.7490,
                'longitude': 37.5390,
                'price': 2000,
                'category_name': '🔧 Мастер-классы',
                'max_participants': 30
            },
            {
                'title': 'Джазовый вечер',
                'description': 'Живая джазовая музыка в уютной атмосфере. Выступление известных музыкантов.',
                'location': 'Москва, Камергерский переулок, 6',
                'latitude': 55.7600,
                'longitude': 37.6135,
                'price': 1200,
                'category_name': '🎵 Концерты',
                'max_participants': 80
            }
        ]
        
        created_count = 0
        for i, event_data in enumerate(sample_events):
            start_date = timezone.now() + timedelta(days=i+1)
            end_date = start_date + timedelta(hours=3)
            
            # Получаем категорию
            try:
                category = Category.objects.get(name=event_data['category_name'])
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Категория не найдена: {event_data["category_name"]}'))
                continue
            
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    'description': event_data['description'],
                    'location': event_data['location'],
                    'latitude': event_data['latitude'],
                    'longitude': event_data['longitude'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'price': event_data['price'],
                    'category': category,
                    'organizer': user,
                    'max_participants': event_data['max_participants'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Создано мероприятие: {event.title}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"ℹ Мероприятие уже существует: {event.title}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Обработка завершена. Создано {created_count} новых мероприятий")
        )