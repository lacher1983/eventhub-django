# 🎉 EventHub - Платформа мероприятий

<div align="center">

![EventHub](https://img.shields.io/badge/EventHub-Django%20Project-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Django](https://img.shields.io/badge/Django-5.2-orange)

*Объединяем людей через события*

</div>

## 🌟 Особенности

- 🤖 **AI-рекомендации** мероприятий
- 🗺️ **Интерактивная карта** событий
- 👥 **Система попутчиков** для мероприятий
- 📱 **Telegram бот** для уведомлений
- 💳 **Онлайн-оплата** билетов
- 🌐 **Мультиязычность** (русский/английский)
- 🎯 **Умная аналитика** и статистика

## 🚀 Быстрый старт

### Вариант 1: Docker (рекомендуется)
```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/eventhub-django.git
cd eventhub-django

# Запускаем через Docker Compose
docker-compose up -d

# Применяем миграции
docker-compose exec web python manage.py migrate

# Создаем суперпользователя
docker-compose exec web python manage.py createsuperuser

# Загружаем тестовые данные
docker-compose exec web python manage.py create_ads
docker-compose exec web python manage.py seed_events

# Устанавливаем зависимости
pip install -r requirements.txt

# Настраиваем базу данных
python manage.py migrate

# Запускаем Redis для Celery
redis-server

# В одном терминале - Celery worker
celery -A config worker -l info

# В другом терминале - Celery beat
celery -A config beat -l info

# В третьем терминале - Django сервер
python manage.py runserver

eventhub-django/
├── events/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── eventhub/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── manage.py
└── requirements.txt


🎯 Роли пользователей
👤 Обычный пользователь - просмотр, регистрация, избранное

🎪 Организатор - создание и управление мероприятиями

👑 Администратор - полный доступ к системе

🔧 API Endpoints
GET /api/events/ - список мероприятий

POST /api/events/{id}/register/ - регистрация

GET /api/users/me/ - профиль пользователя

🤝 Разработка
Для запуска в режиме разработки:
bash
python manage.py runserver 0.0.0.0:8000

📞 Поддержка
По вопросам и предложениям: your-email@example.com