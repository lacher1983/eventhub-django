#!/bin/bash
# entrypoint.sh

# Ожидание доступности PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Ожидание доступности Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Применение миграций
echo "Applying migrations..."
python manage.py migrate --noinput

# Сборка статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Создание суперпользователя (опционально)
echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Загрузка тестовых данных
echo "Loading test data..."
python manage.py loaddata categories.json events.json

exec "$@"