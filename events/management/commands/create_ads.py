from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Advertisement
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create sample advertisements'

    def handle(self, *args, **options):
        # что-то тут не пошло.удалим старые тестовые баннеры
        Advertisement.objects.filter(title__contains="Скидка").delete()
        Advertisement.objects.filter(title__contains="Главное событие").delete()

        ads_data = [
            {
                'title': ' Скидка 20% на все мероприятия!',
                'ad_type': 'banner',
                'position': 'top',
                'content': 'Успейте забронировать! Ограниченное предложение до конца месяца',
                'link': 'https://example.com/promo',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'is_active': True
            },
            {
                'title': ' Главное событие месяца',
                'ad_type': 'video', 
                'position': 'sidebar',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'link': 'https://example.com/main-event',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=60),
                'is_active': True
            },
            {
                'title': ' Премиум-мероприятия со скидкой',
                'ad_type': 'banner',
                'position': 'between_events',
                'content': 'Только этой недели скидки на премиум-мероприятия',
                'link': 'https://example.com/premium',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True
            },
            {
                'title': ' Не пропустите лучшие события',
                'ad_type': 'banner', 
                'position': 'bottom',
                'content': 'Подпишитесь на рассылку и получайте уведомления',
                'link': 'https://example.com/newsletter',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=90),
                'is_active': True
            }
        ]
        
        created_count = 0
        for ad_data in ads_data:
            ad, created = Advertisement.objects.get_or_create(
                title=ad_data['title'],
                defaults=ad_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f' Создан баннер: {ad.title}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f' Баннер уже существует: {ad.title}'))
        
        if created_count == 0:
            self.stdout.write(self.style.WARNING('ℹ Новые баннеры не созданы (возможно уже существуют)'))
        else:
            self.stdout.write(self.style.SUCCESS(f' Создано {created_count} баннеров!'))