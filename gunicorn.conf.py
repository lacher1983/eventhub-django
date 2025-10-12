import multiprocessing
import os

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Сокет для связи с nginx
bind = 'unix:/tmp/gunicorn.sock'

# Параметры воркеров
worker_class = 'sync'
worker_connections = 1000
timeout = 30
max_requests = 1000
max_requests_jitter = 100

# Логирование
accesslog = os.path.join(BASE_DIR, 'logs/gunicorn_access.log')
errorlog = os.path.join(BASE_DIR, 'logs/gunicorn_error.log')
loglevel = 'info'

# Перезагрузка при изменении кода (только для разработки)
reload = False

# Предзагрузка приложения
preload_app = True

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=eventhub.settings.production',
]

# Запуск от имени пользователя (раскомментировать после настройки)
# user = 'webuser'
# group = 'webgroup'