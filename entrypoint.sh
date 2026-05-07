#!/bin/sh
set -e

echo "=== Настройка cron ==="
crontab /app/crontab.txt
service cron start

echo "=== Применяем миграции ==="
python manage.py migrate --noinput

echo "=== Собираем статику ==="
python manage.py collectstatic --noinput

echo "=== Запускаем Gunicorn ==="
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3