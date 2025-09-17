import os
import django
import datetime
from django.utils import timezone
from django.core.files import File
from PIL import Image
import io
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from events.models import Event, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def create_sample_image(width=300, height=200, color='blue', text='Event'):
    try:
        # Создаем изображение
        img = Image.new('RGB', (width, height), color=color)
        
        # Добавляем текст (опционально)
        from PIL import ImageDraw, ImageFont
        try:
            draw = ImageDraw.Draw(img)
            # Попробуем использовать стандартный шрифт
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Центрируем текст
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 2
            
            draw.text((x, y), text, fill='white', font=font)
        except:
            pass  # Если не получилось добавить текст - ну и ничего страшного
        
        # Сохраняем в буфер
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return File(img_io, name=f'{text.lower().replace(" ", "_")}.jpg')
    except Exception as e:
        print(f"Ошибка создания изображения: {e}")
        return None

def create_events():
    """ Создает тестовые события """
    try:
        # Получаем пользователя 
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            print("❌ Пользователь 'admin' не найден. Создайте его сначала.")
            print("   Выполните: python manage.py createsuperuser --username admin")
            return
    
        # Создаем или получаем категории
        education, created = Category.objects.get_or_create(
            name="Образование", 
            slug="education",
            defaults={'description': 'Образовательные мероприятия и вебинары'}
        )
        
        art, created = Category.objects.get_or_create(
            name="Искусство", 
            slug="art",
            defaults={'description': 'Выставки, галереи и художественные события'}
        )
        
        print("🎨 Категории готовы")
    
        # Событие 4: Онлайн-вебинар
        event4 = Event.objects.create(
            title="Digital Marketing Webinar",
            short_description="Продвинутые стратегии цифрового маркетинга",
            description="""Присоединяйтесь к нашему эксклюзивному вебинару, где мы раскроем:
• Тренды digital-маркетинга 2025
• Эффективные инструменты SMM
• SEO-оптимизация для роста трафика
• Кейсы успешных кампаний

Ведущий: Иван Петров, эксперт с 10-летним опытом""",
            date=timezone.now() + datetime.timedelta(days=7),
            location="Онлайн-платформа Zoom",
            event_type="online",
            category=education,
            organizer=admin_user,
            price=0,
            capacity=1000
        )

        # Добавляем изображение для вебинара
        webinar_image = create_sample_image(color='#2c5aa0', text='Digital Marketing')
        if webinar_image:
            event4.image.save('digital_marketing_webinar.jpg', webinar_image)
        
        print(" Вебинар создан")
    
        # Событие 5: Выставка искусств
        event5 = Event.objects.create(
            title="Современное Искусство",
            short_description="Эксклюзивная выставка современных художников",
            description="""Приглашаем на уникальную выставку, представляющую лучшие работы современных русских художников. 

В экспозиции:
• Картины молодых талантов
• Инсталляции и медиа-арт
• Скульптуры и арт-объекты
• Экскурсии с искусствоведами

Дата: 15 октября - 15 ноября 2025
Время: 11:00 - 20:00, ежедневно""",
            date=timezone.now() + datetime.timedelta(days=30),
            location="Москва, Государственная Третьяковская Галерея, Лаврушинский переулок, 10",
            event_type="offline",
            category=art,
            organizer=admin_user, 
            price=1500,
            capacity=200,
            is_active=True
        )
    
        # Добавляем изображение для выставки
        art_image = create_sample_image(color='#8e44ad', text='Art Exhibition')
        if art_image:
            event5.image.save('art_exhibition.jpg', art_image)
        
        print("✅ Выставка создана")
    
    
        # Событие 6: Технологическая конференция (дополнительное)
        tech, created = Category.objects.get_or_create(
            name="Технологии", 
            slug="technology",
            defaults={'description': 'Технологические конференции и IT-мероприятия'}
        )
        
        event6 = Event.objects.create(
            title="TechConf 2025",
            short_description="Главная технологическая конференция года",
            description="""Крупнейшая конференция о технологиях и инновациях. 
Примите участие в дискуссиях о будущем IT, искусственного интеллекта и цифровой трансформации.

Основные темы:
• Искусственный интеллект и машинное обучение
• Кибербезопасность и блокчейн
• Cloud computing и DevOps
• Стартапы и венчурные инвестиции""",
            date=timezone.now() + datetime.timedelta(days=45, hours=10),
            location="Москва, Крокус Сити Холл",
            event_type="offline",
            category=tech,
            organizer=admin_user,
            price=5000,
            capacity=1000,
            is_active=True
        )
        
        tech_image = create_sample_image(color='#27ae60', text='TechConf 2024')
        if tech_image:
            event6.image.save('techconf_2025.jpg', tech_image)
        
        print("✅ Техконференция создана")

        # Красивое завершение
        print("\n" + "="*50)
        print("🎉 События успешно созданы!")
        print("="*50)
        print(f"📚 Образовательный вебинар: {event4.title}")
        print(f"🎨 Художественная выставка: {event5.title}")  
        print(f"💻 Технологическая конференция: {event6.title}")
        print("="*50)
        print("Посмотрите результаты по адресу: http://127.0.0.1:8000/")
    
    except Exception as e:
        print(f"❌ Ошибка при создании событий: {e}")
        import traceback
        traceback.print_exc()
        
    
if __name__ == "__main__":
    print(" Запуск создания тестовых событий...")
    print(" Пожалуйста, подождите...")
    create_events()