
from django.core.management.base import BaseCommand
from events.models import ProjectPromoVideo

class Command(BaseCommand):
    help = 'Создает демо проморолик проекта'
    
    def handle(self, *args, **options):
        # Создаем главный проморолик
        promo, created = ProjectPromoVideo.objects.get_or_create(
            video_type='main',
            defaults={
                'title': 'EventHub - Платформа для мероприятий',
                'description': 'Обзор возможностей платформы EventHub для организаторов и участников мероприятий',
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Заменить на реальный URL
                'is_active': True,
                'show_on_homepage': True,
                'show_on_landing': True,
                'display_order': 1,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Демо проморолик создан!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('ℹ️ Демо проморолик уже существует')
            )