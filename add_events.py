import os
import django
import datetime
from django.utils import timezone
from django.core.files import File
from PIL import Image, ImageDraw, ImageFont
import io
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from events.models import Event, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def create_thematic_image(width=400, height=300, theme='default', title='Event', emoji='🎉'):
    """Создание тематического изображения для мероприятия"""
    try:
        # Цветовые схемы для разных тем
        color_schemes = {
            'ai': {'bg_color': '#1a1a2e', 'gradient_start': '#16213e', 'gradient_end': '#0f3460', 'text_color': '#e94560', 'accent': '#f5f5f5'},
            'python': {'bg_color': '#2b5b84', 'gradient_start': '#306998', 'gradient_end': '#ffd43b', 'text_color': '#ffffff', 'accent': '#ffd43b'},
            'startup': {'bg_color': '#0c4b33', 'gradient_start': '#0c4b33', 'gradient_end': '#28a745', 'text_color': '#ffffff', 'accent': '#ffc107'},
            'art': {'bg_color': '#6a0dad', 'gradient_start': '#8a2be2', 'gradient_end': '#da70d6', 'text_color': '#ffffff', 'accent': '#ffeb3b'},
            'health': {'bg_color': '#1b5e20', 'gradient_start': '#2e7d32', 'gradient_end': '#4caf50', 'text_color': '#ffffff', 'accent': '#c8e6c9'},
            'food': {'bg_color': '#e65100', 'gradient_start': '#ff6f00', 'gradient_end': '#ff9800', 'text_color': '#ffffff', 'accent': '#ffe0b2'},
            'music': {'bg_color': '#01579b', 'gradient_start': '#0277bd', 'gradient_end': '#4fc3f7', 'text_color': '#ffffff', 'accent': '#e1f5fe'},
            'career': {'bg_color': '#37474f', 'gradient_start': '#455a64', 'gradient_end': '#78909c', 'text_color': '#ffffff', 'accent': '#cfd8dc'},
            'charity': {'bg_color': '#b71c1c', 'gradient_start': '#c62828', 'gradient_end': '#ef5350', 'text_color': '#ffffff', 'accent': '#ffcdd2'},
            'networking': {'bg_color': '#004d40', 'gradient_start': '#00695c', 'gradient_end': '#009688', 'text_color': '#ffffff', 'accent': '#b2dfdb'},
            'default': {'bg_color': '#667eea', 'gradient_start': '#667eea', 'gradient_end': '#764ba2', 'text_color': '#ffffff', 'accent': '#ffffff'}
        }
        
        scheme = color_schemes.get(theme, color_schemes['default'])

        # Создаем изображение
        img = Image.new('RGB', (width, height), color=scheme['bg_color'])
        draw = ImageDraw.Draw(img)
        
        # Рисуем градиентный фон
        for i in range(height):
            ratio = i / height
            r1, g1, b1 = [int(c, 16) for c in (scheme['gradient_start'][1:3], scheme['gradient_start'][3:5], scheme['gradient_start'][5:7])]
            r2, g2, b2 = [int(c, 16) for c in (scheme['gradient_end'][1:3], scheme['gradient_end'][3:5], scheme['gradient_end'][5:7])]
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Добавляем декоративные элементы в зависимости от темы
        if theme == 'ai':
            # Нейросеть - добавляем точки как нейроны
            for _ in range(50):
                x = np.random.randint(0, width)
                y = np.random.randint(0, height)
                size = np.random.randint(1, 4)
                draw.ellipse([x, y, x+size, y+size], fill=scheme['accent'])
        
        # Добавляем большой эмодзи
        try:
            font_large = ImageFont.truetype("arial.ttf", 80)
            bbox = draw.textbbox((0, 0), emoji, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 3
            draw.text((x, y), emoji, fill=scheme['accent'], font=font_large)
        except:
            # Если шрифт не доступен, просто рисуем эмодзи
            pass
        
        # Добавляем заголовок
        try:
            font_title = ImageFont.truetype("arial.ttf", 20)
            # Разбиваем заголовок на строки если нужно
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_title)
                test_width = bbox[2] - bbox[0]
                
                if test_width <= width - 40:  # 20px padding с каждой стороны
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Ограничиваем количество строк
            lines = lines[:2]
            
            # Рисуем строки
            line_height = 25
            total_height = len(lines) * line_height
            start_y = height - total_height - 60
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font_title)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) / 2
                y = start_y + i * line_height
                draw.text((x, y), line, fill=scheme['text_color'], font=font_title)
                
        except:
            # Простой текст если шрифт не доступен
            title_short = title[:20] + '...' if len(title) > 20 else title
            draw.text((50, height - 80), title_short, fill=scheme['text_color'])
        
        # Добавляем декоративную линию
        draw.line([(50, height - 40), (width - 50, height - 40)], fill=scheme['accent'], width=2)
        
        # Сохраняем в буфер
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)
        return File(img_io, name=f'{theme}_{title[:10].lower().replace(" ", "_")}.jpg')
        
    except Exception as e:
        print(f"Ошибка создания изображения для темы {theme}: {e}")
        return None

# def create_sample_image(width=300, height=200, color='blue', text='Event'):
#     try:
#         # Создаем изображение
#         img = Image.new('RGB', (width, height), color=color)
        
#         # Добавляем текст (опционально)
#         from PIL import ImageDraw, ImageFont
#         try:
#             draw = ImageDraw.Draw(img)
#             # Попробуем использовать стандартный шрифт
#             try:
#                 font = ImageFont.truetype("arial.ttf", 20)
#             except:
#                 font = ImageFont.load_default()
            
#             # Центрируем текст
#             bbox = draw.textbbox((0, 0), text, font=font)
#             text_width = bbox[2] - bbox[0]
#             text_height = bbox[3] - bbox[1]
#             x = (width - text_width) / 2
#             y = (height - text_height) / 2
            
#             draw.text((x, y), text, fill='white', font=font)
#         except:
#             pass  # Если не получилось добавить текст - ну и ничего страшного
        
#         # Сохраняем в буфер
#         img_io = io.BytesIO()
#         img.save(img_io, format='JPEG', quality=85)
#         img_io.seek(0)
#         return File(img_io, name=f'{text.lower().replace(" ", "_")}.jpg')
#     except Exception as e:
#         print(f"Ошибка создания изображения: {e}")
#         return None

def create_events():
    """Создание демонстрационных мероприятий с тематическими изображениями"""
    try:
        # Получаем администратора
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            print("❌ Пользователь 'admin' не найден. Создайте его сначала.")
            print("   Выполните: python manage.py createsuperuser --username admin")
            return
    
        # Создаем или получаем категории
        categories = {}
        for cat_data in [
            {'name': 'Технологии', 'slug': 'technology', 'emoji': '💻', 'color': '#667eea'},
            {'name': 'Образование', 'slug': 'education', 'emoji': '📚', 'color': '#4facfe'},
            {'name': 'Бизнес', 'slug': 'business', 'emoji': '💼', 'color': '#43e97b'},
            {'name': 'Искусство', 'slug': 'art', 'emoji': '🎨', 'color': '#fa709a'},
            {'name': 'Спорт', 'slug': 'sports', 'emoji': '⚽', 'color': '#a3bded'},
            {'name': 'Музыка', 'slug': 'music', 'emoji': '🎵', 'color': '#f6d365'},
            {'name': 'Еда', 'slug': 'food', 'emoji': '🍕', 'color': '#ffecd2'},
            {'name': 'Здоровье', 'slug': 'health', 'emoji': '💊', 'color': '#84fab0'},
        ]:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                slug=cat_data['slug'],
                defaults={'description': f'{cat_data["name"]} мероприятия'}
            )
            categories[cat_data['slug']] = category
        
        print("✅ Категории созданы")
        
        # Создаем теги
        tags = {}
        tag_data = [
            'python', 'ai', 'машинное обучение', 'вебинар', 'воркшоп', 
            'конференция', 'стартапы', 'нетворкинг', 'онлайн', 'оффлайн'
        ]
        
        for tag_name in tag_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name, 'color': '#007bff'}
            )
            tags[tag_name] = tag
        
        print("✅ Теги созданы")

        # 10 мероприятий с уникальными тематическими изображениями
        demo_events = [
            {
                'title': 'AI Conference 2025 - Будущее искусственного интеллекта',
                'short_description': 'Крупнейшая конференция по искусственному интеллекту и машинному обучению в России',
                'description': """Присоединяйтесь к ведущим экспертам в области искусственного интеллекта на самой масштабной конференции года!""",
                'date': timezone.now() + datetime.timedelta(days=10),
                'location': 'Москва, Крокус Сити Холл',
                'category_slug': 'technology',
                'event_type': 'conference',
                'event_format': 'offline',
                'price': 5000,
                'capacity': 1000,
                'theme': 'ai',
                'emoji': '🤖',
                'tags': ['ai', 'машинное обучение', 'конференция']
            },
            {
                'title': 'Python Mastery: От новичка до профессионала',
                'short_description': 'Интенсивный курс по Python с нуля до продвинутого уровня',
                'description': """Освойте один из самых востребованных языков программирования под руководством опытных менторов!""",
                'date': timezone.now() + datetime.timedelta(days=5),
                'location': 'Онлайн (Zoom + Discord)',
                'category_slug': 'education',
                'event_type': 'course',
                'event_format': 'online',
                'price': 15000,
                'capacity': 50,
                'theme': 'python',
                'emoji': '🐍',
                'tags': ['python', 'вебинар', 'онлайн']
            },
            {
                'title': 'Стартап Уикенд: От идеи к продукту',
                'short_description': 'Практический воркшоп по созданию и запуску стартапов',
                'description': """Превратите свою идею в работающий бизнес за один уикенд!""",
                'date': timezone.now() + datetime.timedelta(days=15),
                'location': 'Москва, Коворкинг "Точка кипения"',
                'category_slug': 'business',
                'event_type': 'workshop',
                'event_format': 'offline',
                'price': 3000,
                'capacity': 100,
                'theme': 'startup',
                'emoji': '🚀',
                'tags': ['стартапы', 'воркшоп', 'нетворкинг']
            },
            {
                'title': 'Выставка современного искусства "Авангард 2025"',
                'short_description': 'Эксклюзивная выставка работ молодых российских художников',
                'description': """Откройте для себя новое поколение российских художников на самой ожидаемой выставке сезона!""",
                'date': timezone.now() + datetime.timedelta(days=20),
                'location': 'Москва, Центр современного искусства "Винзавод"',
                'category_slug': 'art',
                'event_type': 'exhibition_culture',
                'event_format': 'offline',
                'price': 500,
                'capacity': 500,
                'theme': 'art',
                'emoji': '🎨',
                'tags': ['искусство', 'выставка', 'оффлайн']
            },
            {
                'title': 'Марафон здорового образа жизни',
                'short_description': '21-дневный онлайн-марафон по формированию здоровых привычек',
                'description': """Преобразите свое тело и сознание за 21 день под руководством экспертов!""",
                'date': timezone.now() + datetime.timedelta(days=3),
                'location': 'Онлайн-платформа',
                'category_slug': 'health',
                'event_type': 'training',
                'event_format': 'online',
                'price': 2500,
                'capacity': 200,
                'theme': 'health',
                'emoji': '💪',
                'tags': ['здоровье', 'онлайн', 'тренировки']
            },
            {
                'title': 'Фестиваль уличной еды "Food Truck Battle"',
                'short_description': 'Крупнейший фестиваль уличной еды с участием лучших фудтраков города',
                'description': """Погрузитесь в мир гастрономических удовольствий на самом вкусном фестивале лета!""",
                'date': timezone.now() + datetime.timedelta(days=25),
                'location': 'Москва, Парк Горького',
                'category_slug': 'food',
                'event_type': 'festival',
                'event_format': 'offline',
                'price': 0,
                'capacity': 5000,
                'theme': 'food',
                'emoji': '🍕',
                'tags': ['еда', 'фестиваль', 'бесплатно']
            },
            {
                'title': 'Концерт классической музыки в планетарии',
                'short_description': 'Уникальное сочетание классической музыки и визуального шоу под куполом планетария',
                'description': """Испытайте незабываемые эмоции от синтеза классической музыки и космической визуализации!""",
                'date': timezone.now() + datetime.timedelta(days=30),
                'location': 'Москва, Планетарий',
                'category_slug': 'music',
                'event_type': 'concert',
                'event_format': 'offline',
                'price': 2000,
                'capacity': 300,
                'theme': 'music',
                'emoji': '🎵',
                'tags': ['музыка', 'концерт', 'искусство']
            },
            {
                'title': 'Бесплатный вебинар: Карьера в IT 2025',
                'short_description': 'Как построить успешную карьеру в IT в 2025 году - тренды и возможности',
                'description': """Узнайте, какие профессии будут востребованы в IT в 2025 году и как подготовиться к ним уже сейчас!""",
                'date': timezone.now() + datetime.timedelta(days=2),
                'location': 'Онлайн (YouTube трансляция)',
                'category_slug': 'education',
                'event_type': 'webinar',
                'event_format': 'online',
                'price': 0,
                'capacity': 1000,
                'theme': 'career',
                'emoji': '💼',
                'tags': ['карьера', 'вебинар', 'бесплатно']
            },
            {
                'title': 'Благотворительный забег "Бежим от рака"',
                'short_description': 'Ежегодный благотворительный забег в поддержку онкологических больных',
                'description': """Присоединяйтесь к благотворительному забегу и помогите собрать средства для лечения онкологических больных!""",
                'date': timezone.now() + datetime.timedelta(days=35),
                'location': 'Москва, Парк Победы',
                'category_slug': 'sports',
                'event_type': 'sport_event',
                'event_format': 'offline',
                'price': 1000,
                'capacity': 2000,
                'theme': 'charity',
                'emoji': '❤️',
                'tags': ['благотворительность', 'спорт', 'забег']
            },
            {
                'title': 'Нетворкинг для IT-специалистов "Tech Connect"',
                'short_description': 'Вечер нетворкинга для разработчиков, дизайнеров и IT-менеджеров',
                'description': """Расширьте свои профессиональные связи на самом технологичном нетворкинге города!""",
                'date': timezone.now() + datetime.timedelta(days=7),
                'location': 'Москва, Лофт "Благодать"',
                'category_slug': 'business',
                'event_type': 'networking',
                'event_format': 'offline',
                'price': 1500,
                'capacity': 150,
                'theme': 'networking',
                'emoji': '🤝',
                'tags': ['нетворкинг', 'it', 'оффлайн']
            }
        ]
        
        created_count = 0
        for event_data in demo_events:
            # Проверяем, существует ли уже мероприятие
            if not Event.objects.filter(title=event_data['title']).exists():
                # Получаем объект категории по slug
                category_slug = event_data['category_slug']
                if category_slug in categories:
                    category_obj = categories[category_slug]
                else:
                    print(f"❌ Категория {category_slug} не найдена")
                    continue
                
                # Создаем тематическое изображение
                event_image = create_thematic_image(
                    theme=event_data['theme'],
                    title=event_data['title'],
                    emoji=event_data['emoji']
                )
                
                # Создаем мероприятие
                event = Event.objects.create(
                    title=event_data['title'],
                    short_description=event_data['short_description'],
                    description=event_data['description'],
                    date=event_data['date'],
                    location=event_data['location'],
                    category=category_obj,
                    event_type=event_data['event_type'],
                    event_format=event_data['event_format'],
                    price=event_data['price'],
                    capacity=event_data['capacity'],
                    organizer=admin_user,
                    is_active=True
                )
                
                # Добавляем изображение
                if event_image:
                    event.image.save(f"{event_data['theme']}_{event_data['title'][:10].lower().replace(' ', '_')}.jpg", event_image)
                    print(f"🎨 Создано тематическое изображение для: {event_data['title']}")
                
                # Добавляем теги
                for tag_name in event_data['tags']:
                    if tag_name in tags:
                        event.tags.add(tags[tag_name])
                
                event.save()
                created_count += 1
                print(f"✅ Создано мероприятие: {event_data['title']}")
            else:
                print(f"ℹ️ Уже существует: {event_data['title']}")
        
        # Итоговый отчет
        print("\n" + "="*60)
        print("🎉 ДЕМО-МЕРОПРИЯТИЯ С ТЕМАТИЧЕСКИМИ ИЗОБРАЖЕНИЯМИ СОЗДАНЫ!")
        print("="*60)
        print(f"📊 Создано мероприятий: {created_count}/10")
        print(f"🎨 Тематические изображения: {created_count}")
        print(f"📚 Категорий: {Category.objects.count()}")
        print(f"🏷️ Тегов: {Tag.objects.count()}")
        print("="*60)
        print("🌐 Посмотреть красивые карточки: http://127.0.0.1:8000/")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка при создании мероприятий: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск создания мероприятий с тематическими изображениями...")
    print("⏳ Создаем уникальные дизайны для каждого мероприятия...")
    create_events()

