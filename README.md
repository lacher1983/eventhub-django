README.md:
# EventHub - Платформа мероприятий

Django-приложение для организации и управления мероприятиями.

## 🚀 Возможности

- Создание и управление мероприятиями
- Регистрация на мероприятия
- Система категорий
- Поиск и фильтрация

## 🛠️ Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Примените миграции: `python manage.py migrate`
4. Запустите сервер: `python manage.py runserver`
5. python manage.py createsuperuser --username admin --email admin@example.com
6. python add_events.py  # или python scripts/add_events.py, если вынесли

## 🐳 Docker Deployment
### Quick Start with Docker
1. **Clone the repository**
```bash
git clone <repository-url>
cd EventHub

## Версии
0. нулевая версия потерялася
1. main/master - старая версия проекта
2.refactored-version - новая исправленная версия

# Для работы со старой версией
git checkout main
# Для работы с новой версией  
git checkout refactored-version