from django.core.management.base import BaseCommand
from events.models import Event
from django.db.models import Q

class Command(BaseCommand):
    help = 'Обновляет координаты для всех мероприятий без координат'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Обновить координаты для всех мероприятий',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Размер батча для обработки',
        )
    
    def handle(self, *args, **options):
        # Проверяем доступность geopy
        try:
            from geopy.geocoders import Nominatim
            geopy_available = True
        except ImportError:
            self.stdout.write(
                self.style.ERROR('Geopy не установлен. Установите: pip install geopy')
            )
            return
        
        if options['force']:
            events = Event.objects.filter(is_active=True)
            self.stdout.write(f"Обновление координат для всех {events.count()} мероприятий...")
        else:
            events = Event.objects.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True),
                is_active=True
            )
            self.stdout.write(f"Обновление координат для {events.count()} мероприятий без координат...")
        
        updated_count = 0
        batch_size = options['batch_size']
        
        for i in range(0, events.count(), batch_size):
            batch = events[i:i + batch_size]
            
            for event in batch:
                old_lat = event.latitude
                old_lon = event.longitude
                
                event.geocode_location()
                
                if event.latitude != old_lat or event.longitude != old_lon:
                    event.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {event.title}: {event.latitude}, {event.longitude}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  {event.title}: координаты не изменились"
                        )
                    )
            
            self.stdout.write(f"Обработано {min(i + batch_size, events.count())} из {events.count()}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Обновлено {updated_count} мероприятий из {events.count()}"
            )
        )