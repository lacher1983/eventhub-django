from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import ExternalEventSource, ExternalEvent
from events.parsers import get_parser
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from events.parsers import get_parser
except ImportError as e:
    print(f"Import error: {e}")
    print("Current Python path:", sys.path)
    raise

import logging


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Синхронизирует мероприятия из внешних источников'
    
    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, help='ID источника для синхронизации')
        parser.add_argument('--archive-old', action='store_true', help='Архивировать старые мероприятия')
    
    def handle(self, *args, **options):
        # Архивация старых мероприятий
        if options['archive_old']:
            self.archive_old_events()
        
        # Синхронизация мероприятий
        sources = ExternalEventSource.objects.filter(is_active=True)
        if options['source']:
            sources = sources.filter(id=options['source'])
        
        for source in sources:
            self.sync_source(source)
    
    def sync_source(self, source):
        """Синхронизирует мероприятия из одного источника"""
        self.stdout.write(f"Синхронизация {source.name}...")
        
        try:
            parser = get_parser(source)
            events_data = parser.parse_events()
            
            created_count = 0
            updated_count = 0
            
            for event_data in events_data:
                if not event_data:
                    continue


                external_id = event_data['external_id']
                
                # Проверяем, существует ли уже такое мероприятие
                event, created = ExternalEvent.objects.get_or_create(
                    source=source,
                    external_id=external_id,
                    defaults=event_data
                )
                
                if not created:
                    # Обновляем существующее мероприятие
                    for key, value in event_data.items():
                        if key != 'external_id':
                            setattr(event, key, value)
                    event.save()
                    updated_count += 1
                else:
                    created_count += 1
            
            source.last_sync = timezone.now()
            source.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"{source.name}: создано {created_count}, обновлено {updated_count}"
                )
            )
            
        except Exception as e:
            logger.error(f"Error syncing {source.name}: {e}")
            self.stdout.write(
                self.style.ERROR(f"Ошибка синхронизации {source.name}: {e}")
            )
    
    def archive_old_events(self):
        """Архивирует мероприятия, которые уже прошли"""
        old_events = ExternalEvent.objects.filter(
            date__lt=timezone.now(),
            is_archived=False
        )
        
        count = old_events.count()
        old_events.update(is_archived=True)
        
        self.stdout.write(
            self.style.SUCCESS(f"Заархивировано {count} старых мероприятий")
        )