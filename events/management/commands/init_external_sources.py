from django.core.management.base import BaseCommand
from events.models import ExternalEventSource
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Инициализирует внешние источники мероприятий'
    
    def handle(self, *args, **options):
        sources = [
            {
                'name': 'Bezkassira.by',
                'url': 'https://bezkassira.by/',
                'parser_config': {}
            },
            {
                'name': 'Relax.by Афиша',
                'url': 'https://afisha.relax.by/',
                'parser_config': {}
            },
            {
                'name': 'Culture.ru Афиша',
                'url': 'https://www.culture.ru/afisha/russia', 
                'parser_config': {}
            },
            {
                'name': 'Events in Russia',
                'url': 'https://eventsinrussia.com/',
                'parser_config': {}
            },
        ]
        
        created_count = 0
        for source_data in sources:
            source, created = ExternalEventSource.objects.get_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Создан источник: {source.name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Источник уже существует: {source.name}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Инициализация завершена. Создано источников: {created_count}")
        )