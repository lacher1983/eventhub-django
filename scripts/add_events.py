import os
import django
import datetime
from django.utils import timezone
from django.core.files import File
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ВРЕМЕННО отключаем проблемные сигналы
from django.db.models.signals import post_save
from events import models as events_models

# Отключаем сигнал, который вызывает ошибку
try:
    post_save.disconnect(events_models.notify_subscribers, sender=events_models.Event)
except:
    pass

from events.models import Event, Category, Tag
from django.contrib.auth import get_user_model

User = get_user_model()

def create_sample_image(width=400, height=300, color='#667eea', text='Event', emoji='🎉'):
    """Создание красивого изображения для мероприятия"""
    try:
        # Создаем изображение с градиентом
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        draw .rectangle([0, 0, width, height], outline=scheme['accent'], width=4)  # рамка

        # Рисуем градиентный фон
        for i in range(height):
            r = int(int(color[1:3], 16) * (height - i) / height)
            g = int(int(color[3:5], 16) * (height - i) / height)
            b = int(int(color[5:7], 16) * (height - i) / height)
            draw.line([(0, i), (width, i)], fill=(r, g, b))

        # Добавляем эмодзи
        try:
            font_large = ImageFont.truetype("arial.ttf", 80)
            bbox = draw.textbbox((0, 0), emoji, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 2 - 20
            draw.text((x, y), emoji, fill='white', font=font_large)
        except:
            pass
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2
            y = height - 80
            draw.text((x, y), text, fill='white', font=font)
        except:
            pass

        # Сохраняем в буфер
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=90)
        img_io.seek(0)
        return File(img_io, name=f'{text.lower().replace(" ", "_")}.jpg')
    except Exception as e:
        print(f"Ошибка создания изображения: {e}")
        return None

def create_events():
    """Создание демонстрационных мероприятий"""
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

        demo_events = [
            {
                'title': 'AI Conference 2025 - Будущее искусственного интеллекта',
                'short_description': 'Крупнейшая конференция по искусственному интеллекту и машинному обучению в России',
                'description': """Присоединяйтесь к ведущим экспертам в области искусственного интеллекта на самой масштабной конференции года!

🎯 Ключевые темы:
• Глубокое обучение и нейронные сети
• Компьютерное зрение и NLP
• AI в бизнесе и промышленности
• Этические аспекты искусственного интеллекта

👥 Спикеры:
- Доктор Иван Петров (Google AI)
- Профессор Мария Сидорова (МГУ)
- Алексей Козлов (Yandex AI)

💡 Что вы получите:
- Практические кейсы внедрения AI
- Нетворкинг с лидерами индустрии
- Доступ к эксклюзивным материалам""",
                'date': timezone.now() + datetime.timedelta(days=10),
                'location': 'Москва, Крокус Сити Холл',
                'category_slug': 'technology',  # Изменено с category на category_slug
                'event_type': 'conference',
                'event_format': 'offline',
                'price': 5000,
                'capacity': 1000,
                'emoji': '🤖',
                'color': '#667eea',
                'tags': ['ai', 'машинное обучение', 'конференция']
            },
            {
                'title': 'Python Mastery: От новичка до профессионала',
                'short_description': 'Интенсивный курс по Python с нуля до продвинутого уровня',
                'description': """Освойте один из самых востребованных языков программирования под руководством опытных менторов!

📚 Программа курса:
• Основы Python: синтаксис и структуры данных
• ООП и паттерны проектирования
• Web-разработка на Django и Flask
• Data Science: pandas, numpy, matplotlib
• Автоматизация и скрипты

🛠 Практика:
- Реальные проекты и кейсы
- Code review от экспертов
- Подготовка портфолио
- Помощь в трудоустройстве

🎓 Формат:
- 48 часов практических занятий
- 12 домашних заданий
- 4 мини-проекта
- Финальный дипломный проект""",
                'date': timezone.now() + datetime.timedelta(days=5),
                'location': 'Онлайн (Zoom + Discord)',
                'category_slug': 'education',
                'event_type': 'course',
                'event_format': 'online',
                'price': 15000,
                'capacity': 50,
                'emoji': '🐍',
                'color': '#4facfe',
                'tags': ['python', 'вебинар', 'онлайн']
            },
            {
                'title': 'Стартап Уикенд: От идеи к продукту',
                'short_description': 'Практический воркшоп по созданию и запуску стартапов',
                'description': """Превратите свою идею в работающий бизнес за один уикенд!

🚀 Что вас ждет:
• Разработка бизнес-модели
• Создание MVP (Minimum Viable Product)
• Привлечение первых клиентов
• Подготовка питча для инвесторов

👨‍💻 Менторы:
- Основатели успешных стартапов
- Бизнес-ангелы и инвесторы
- Эксперты по маркетингу и продажам

🏆 Финальный питч:
- Презентация проектов перед жюри
- Возможность получить финансирование
- Призы от партнеров""",
                'date': timezone.now() + datetime.timedelta(days=15),
                'location': 'Москва, Коворкинг "Точка кипения"',
                'category_slug': 'business',
                'event_type': 'workshop',
                'event_format': 'offline',
                'price': 3000,
                'capacity': 100,
                'emoji': '🚀',
                'color': '#43e97b',
                'tags': ['стартапы', 'воркшоп', 'нетворкинг']
            },
            {
                'title': 'Выставка современного искусства "Авангард 2025"',
                'short_description': 'Эксклюзивная выставка работ молодых российских художников',
                'description': """Откройте для себя новое поколение российских художников на самой ожидаемой выставке сезона!

🎨 Экспозиция:
• Живопись и графика
• Цифровое искусство и инсталляции
• Скульптура и арт-объекты
• Видео-арт и перформансы

👩‍🎨 Участники:
- Победители международных конкурсов
- Выпускники ведущих художественных вузов
- Перспективные молодые художники

📅 Программа:
- Экскурсии с кураторами
- Встречи с художниками
- Арт-перформансы
- Мастер-классы""",
                'date': timezone.now() + datetime.timedelta(days=20),
                'location': 'Москва, Центр современного искусства "Винзавод"',
                'category_slug': 'art',
                'event_type': 'exhibition_culture',
                'event_format': 'offline',
                'price': 500,
                'capacity': 500,
                'emoji': '🎨',
                'color': '#fa709a',
                'tags': ['искусство', 'выставка', 'оффлайн']
            },
            {
                'title': 'Марафон здорового образа жизни',
                'short_description': '21-дневный онлайн-марафон по формированию здоровых привычек',
                'description': """Преобразите свое тело и сознание за 21 день под руководством экспертов!

💪 Программа марафона:
• Персональный план питания
• Ежедневные тренировки разной интенсивности
• Медитации и практики осознанности
• Работа с психологом

🏃‍♀️ Тренеры:
- Сертифицированные фитнес-тренеры
- Диетологи и нутрициологи
- Психологи и коучи

📱 Что входит:
- Ежедневные задания в мобильном приложении
- Закрытый чат с участниками
- Онлайн-трансляции тренировок
- Поддержка кураторов 24/7""",
                'date': timezone.now() + datetime.timedelta(days=3),
                'location': 'Онлайн-платформа',
                'category_slug': 'health',
                'event_type': 'training',
                'event_format': 'online',
                'price': 2500,
                'capacity': 200,
                'emoji': '💪',
                'color': '#84fab0',
                'tags': ['здоровье', 'онлайн', 'тренировки']
            },
            {
                'title': 'Фестиваль уличной еды "Food Truck Battle"',
                'short_description': 'Крупнейший фестиваль уличной еды с участием лучших фудтраков города',
                'description': """Погрузитесь в мир гастрономических удовольствий на самом вкусном фестивале лета!

🍔 Участники:
• 50+ фудтраков с разнообразной кухней
• Крафтовые пивоварни
• Кофейни и десерты
• Вегетарианские и веганские options

🎵 Развлечения:
- Живая музыка и диджеи
- Гастрономические мастер-классы
- Конкурсы и розыгрыши
- Детская зона с анимацией

🏆 Food Truck Battle:
- Битва шеф-поваров
- Народное голосование
- Призы от спонсоров""",
                'date': timezone.now() + datetime.timedelta(days=25),
                'location': 'Москва, Парк Горького',
                'category_slug': 'food',
                'event_type': 'festival',
                'event_format': 'offline',
                'price': 0,
                'capacity': 5000,
                'emoji': '🍕',
                'color': '#ffecd2',
                'tags': ['еда', 'фестиваль', 'бесплатно']
            },
            {
                'title': 'Концерт классической музыки в планетарии',
                'short_description': 'Уникальное сочетание классической музыки и визуального шоу под куполом планетария',
                'description': """Испытайте незабываемые эмоции от синтеза классической музыки и космической визуализации!

🎻 Программа:
• Моцарт - "Волшебная флейта"
• Вивальди - "Времена года" 
• Бетховен - "Лунная соната"
• Чайковский - "Лебединое озеро"

🌌 Визуальное шоу:
- Проекция на куполе планетария
- Космические пейзажи и галактики
- Синхронизация с музыкой
- Эффекты виртуальной реальности

🎫 Особенности:
- Ограниченное количество мест
- Продолжительность 2 часа
- Возрастное ограничение 6+""",
                'date': timezone.now() + datetime.timedelta(days=30),
                'location': 'Москва, Планетарий',
                'category_slug': 'music',
                'event_type': 'concert',
                'event_format': 'offline',
                'price': 2000,
                'capacity': 300,
                'emoji': '🎵',
                'color': '#f6d365',
                'tags': ['музыка', 'концерт', 'искусство']
            },
            {
                'title': 'Бесплатный вебинар: Карьера в IT 2025',
                'short_description': 'Как построить успешную карьеру в IT в 2025 году - тренды и возможности',
                'description': """Узнайте, какие профессии будут востребованы в IT в 2025 году и как подготовиться к ним уже сейчас!

📊 Тренды 2025:
• Самые перспективные IT-профессии
• Необходимые навыки и компетенции
• Уровень зарплат в индустрии
• Удаленная работа и релокация

💼 Карьерные пути:
- Разработка (Frontend, Backend, Mobile)
- Data Science и AI
- DevOps и кибербезопасность
- Продукт-менеджмент

🎯 Практические советы:
- Составление резюме и портфолио
- Подготовка к собеседованиям
- Выбор образовательных программ
- Нетворкинг в IT-сообществе""",
                'date': timezone.now() + datetime.timedelta(days=2),
                'location': 'Онлайн (YouTube трансляция)',
                'category_slug': 'education',
                'event_type': 'webinar',
                'event_format': 'online',
                'price': 0,
                'capacity': 1000,
                'emoji': '💼',
                'color': '#4facfe',
                'tags': ['карьера', 'вебинар', 'бесплатно']
            },
            {
                'title': 'Благотворительный забег "Бежим от рака"',
                'short_description': 'Ежегодный благотворительный забег в поддержку онкологических больных',
                'description': """Присоединяйтесь к благотворительному забегу и помогите собрать средства для лечения онкологических больных!

🏃‍♂️ Дистанции:
• 5 км (любители)
• 10 км (профессионалы)
• 1 км (детский забег)
• 500 м (забег с собаками)

❤️ Благотворительность:
- Все собранные средства направляются в фонд помощи онкобольным
- Каждый участник получает стартовый пакет
- Футболка и медаль финишера

🎉 После забега:
- Награждение победителей
- Концерт и развлечения
- Фудкорт и напитки
- Фотозоны""",
                'date': timezone.now() + datetime.timedelta(days=35),
                'location': 'Москва, Парк Победы',
                'category_slug': 'sports',
                'event_type': 'sport_event',
                'event_format': 'offline',
                'price': 1000,
                'capacity': 2000,
                'emoji': '❤️',
                'color': '#a3bded',
                'tags': ['благотворительность', 'спорт', 'забег']
            },
            {
                'title': 'Нетворкинг для IT-специалистов "Tech Connect"',
                'short_description': 'Вечер нетворкинга для разработчиков, дизайнеров и IT-менеджеров',
                'description': """Расширьте свои профессиональные связи на самом технологичном нетворкинге города!

🤝 Формат:
• Speed-dating с IT-специалистами
• Тематические зоны общения
• Мини-презентации участников
• Неформальное общение

🎯 Для кого:
- Разработчики всех направлений
- Дизайнеры и UX/UI специалисты
- Продукт- и проект-менеджеры
- IT-рекрутеры и HR

🍹 В программе:
- Welcome drink и фуршет
- Интерактивные игры и активности
- Розыгрыш призов от партнеров
- Послепарти в баре""",
                'date': timezone.now() + datetime.timedelta(days=7),
                'location': 'Москва, Лофт "Благодать"',
                'category_slug': 'business',
                'event_type': 'networking',
                'event_format': 'offline',
                'price': 1500,
                'capacity': 150,
                'emoji': '🤝',
                'color': '#43e97b',
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
                
                # Создаем изображение
                event_image = create_sample_image(
                    color=event_data['color'],
                    text=event_data['title'][:20] + '...',
                    emoji=event_data['emoji']
                )
                
                # Создаем мероприятие
                event = Event.objects.create(
                    title=event_data['title'],
                    short_description=event_data['short_description'],
                    description=event_data['description'],
                    date=event_data['date'],
                    location=event_data['location'],
                    category=category_obj,  # Используем объект категории
                    event_type=event_data['event_type'],
                    event_format=event_data['event_format'],
                    price=event_data['price'],
                    capacity=event_data['capacity'],
                    organizer=admin_user,
                    is_active=True
                )
                
                # Добавляем изображение
                if event_image:
                    event.image.save(f"{event_data['title'][:10]}.jpg", event_image)
                
                # Добавляем теги
                for tag_name in event_data['tags']:
                    if tag_name in tags:
                        event.tags.add(tags[tag_name])
                
                event.save()
                created_count += 1
                print(f"✅ Создано: {event_data['title']}")
            else:
                print(f"ℹ️ Уже существует: {event_data['title']}")
        
        # Итоговый отчет
        print("\n" + "="*60)
        print("🎉 ДЕМО-МЕРОПРИЯТИЯ УСПЕШНО СОЗДАНЫ!")
        print("="*60)
        print(f"📊 Создано мероприятий: {created_count}/10")
        print(f"📚 Категорий: {Category.objects.count()}")
        print(f"🏷️ Тегов: {Tag.objects.count()}")
        print("="*60)
        print("🌐 Посмотреть результаты: http://127.0.0.1:8000/")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка при создании мероприятий: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск создания демонстрационных мероприятий...")
    print("⏳ Пожалуйста, подождите...")
    create_events()