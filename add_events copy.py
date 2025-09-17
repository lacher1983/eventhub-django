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

def print_banner(title, color_code="36"):
    """Печатает стильный баннер для события"""
    width = 60
    print(f"\n\033[{color_code}m{'═' * width}\033[0m")
    print(f"\033[{color_code}m{title.center(width)}\033[0m")
    print(f"\033[{color_code}m{'═' * width}\033[0m")

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
        print_banner("🎓 СОЗДАНИЕ ВЕБИНАРА", "36")  # Голубой цвет
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
        
        print("✅ Вебинар создан")
        print(f"   Название: {event4.title}")
        print(f"   Дата: {event4.date.strftime('%d.%m.%Y в %H:%M')}")
        print(f"   Место: {event4.location}")
    
        # Событие 5: Выставка искусств
        print_banner("🎨 СОЗДАНИЕ ВЫСТАВКИ", "35")  # Фиолетовый цвет
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
        print(f"   Название: {event5.title}")
        print(f"   Дата: {event5.date.strftime('%d.%m.%Y в %H:%M')}")
        print(f"   Место: {event5.location}")
        print(f"   Цена: {event5.price} руб.")
    
        # Событие 6: Технологическая конференция
        print_banner("💻 СОЗДАНИЕ КОНФЕРЕНЦИИ", "32")  # Зеленый цвет
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
        
        tech_image = create_sample_image(color='#27ae60', text='TechConf 2025')
        if tech_image:
            event6.image.save('techconf_2025.jpg', tech_image)
        
        print("✅ Техконференция создана")
        print(f"   Название: {event6.title}")
        print(f"   Дата: {event6.date.strftime('%d.%m.%Y в %H:%M')}")
        print(f"   Место: {event6.location}")
        print(f"   Цена: {event6.price} руб.")

        # Итоговый баннер
        print_banner("🎉 СОБЫТИЯ УСПЕШНО СОЗДАНЫ!", "36")
        print("\033[1mСозданные события:\033[0m")
        print("┌───────────────────────────────────────────────┐")
        print(f"│ 📚 \033[36mОбразовательный вебинар:\033[0m {event4.title[:30]}... │")
        print(f"│ 🎨 \033[35mХудожественная выставка:\033[0m {event5.title[:30]}... │")
        print(f"│ 💻 \033[32mТехнологическая конференция:\033[0m {event6.title[:30]}... │")
        print("└───────────────────────────────────────────────┘")
        print()
        print("\033[3mПосмотрите результаты по адресу: http://127.0.0.1:8000/\033[0m")
        print()
    
    except Exception as e:
        print(f"❌ Ошибка при создании событий: {e}")
        import traceback
        traceback.print_exc()
        
    
if __name__ == "__main__":
    print("🚀 Запуск создания тестовых событий...")
    print("⏳ Пожалуйста, подождите...")
    create_events()