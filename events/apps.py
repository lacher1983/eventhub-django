from django.apps import AppConfig

class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # Отложенная загрузка сигналов чтобы избежать предупреждений
        import django
        if not django.setup:
            try:
                import events.signals
                import events.signals_gamification
            except ImportError as e:
                print(f"Warning: Could not import signals: {e}")