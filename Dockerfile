# Dockerfile
FROM python:3.11-slim-bullseye

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя и рабочей директории
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app
USER app

# Создание виртуального окружения
RUN python -m venv venv
ENV PATH="/home/app/venv/bin:$PATH"

# Копирование requirements
COPY --chown=app:app requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# Копирование проекта
COPY --chown=app:app . .

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Порт приложения
EXPOSE 8000

# Команда запуска
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]