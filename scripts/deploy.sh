#!/bin/bash

# Скрипт деплоя для EventHub

set -e

echo "🚀 Starting EventHub deployment..."

# Переменные
PROJECT_DIR="/opt/eventhub"
VENV_DIR="$PROJECT_DIR/venv"
REPO_URL="https://github.com/your-username/eventhub-django.git"
BRANCH="main"

# Создание директорий
echo "📁 Creating directories..."
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $PROJECT_DIR/logs
sudo mkdir -p $PROJECT_DIR/staticfiles
sudo mkdir -p $PROJECT_DIR/media

# Настройка прав
echo "🔑 Setting permissions..."
sudo chown -R $USER:$USER $PROJECT_DIR
chmod 755 $PROJECT_DIR

# Клонирование/обновление кода
echo "📥 Updating code..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd $PROJECT_DIR
    git fetch origin
    git reset --hard origin/$BRANCH
else
    git clone -b $BRANCH $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Создание виртуального окружения
echo "🐍 Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate

# Установка зависимостей
echo "📦 Installing dependencies..."
pip install -U pip
pip install -r requirements/production.txt

# Применение миграций
echo "🗃️ Running migrations..."
python manage.py migrate --settings=eventhub.settings.production

# Сбор статических файлов
echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --settings=eventhub.settings.production

# Загрузка фикстур (если нужно)
# python manage.py loaddata initial_data --settings=eventhub.settings.production

# Перезапуск служб
echo "🔄 Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart celery

# Очистка кэша
echo "🧹 Cleaning cache..."
python manage.py clear_cache --settings=eventhub.settings.production

echo "✅ Deployment completed successfully!"
echo "🌐 Application is live at: https://your-domain.com"