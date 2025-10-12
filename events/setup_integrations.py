import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def setup_environment():
    """Настройка окружения для интеграций"""
    
    # Создание тестовых данных
    from events.management.commands.create_ads import Command as CreateAdsCommand
    from events.management.commands.seed_events import Command as SeedEventsCommand
    
    print("🎯 Настройка EventHub с AI и интеграциями...")
    
    # Создание рекламных баннеров
    ads_command = CreateAdsCommand()
    ads_command.handle()
    
    # Создание тестовых мероприятий
    seed_command = SeedEventsCommand()
    seed_command.handle()
    
    print("✅ Интеграции настроены!")
    print("\n🎉 Доступные функции:")
    print("   🤖 AI-рекомендации мероприятий")
    print("   📱 Telegram уведомления") 
    print("   🌤️ Погодная интеграция")
    print("   📊 Продвинутая аналитика")
    print("   🎨 Интерактивный календарь")

if __name__ == "__main__":
    setup_environment()