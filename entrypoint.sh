#!/bin/sh
set -e

export TZ="${TZ:-Europe/Moscow}"
export DJANGO_SETTINGS_MODULE=config.settings

DB_DIR="${DJANGO_DB_DIR:-/data/db}"
MEDIA_DIR="${DJANGO_MEDIA_ROOT:-/data/media}"
CRON_SCHEDULE="${CRON_EXPIRE_SCHEDULE:-0 3 * * *}"

mkdir -p "$DB_DIR" "$MEDIA_DIR" /var/log /etc/onetwoboard
chmod 755 "$DB_DIR" "$MEDIA_DIR"

echo "=== Часовой пояс: $TZ ==="
echo "=== БД: $DB_DIR | Media: $MEDIA_DIR ==="

echo "=== Сохраняем окружение для cron ==="
{
    echo 'export TZ="'"$TZ"'"'
    echo 'export DJANGO_SETTINGS_MODULE=config.settings'
    printenv | grep -E '^(DJANGO_|ENABLE_|EMAIL_|GOOGLE_|SITE_|NOTIFY_|TZ=)' \
        | sed 's/^/export /' || true
} > /etc/onetwoboard/cron-env.sh

echo "=== Настройка cron ($CRON_SCHEDULE) ==="
cat > /etc/cron.d/onetwoboard-expire <<EOF
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin
$CRON_SCHEDULE root /app/scripts/run_expire.sh >> /var/log/onetwoboard_expire.log 2>&1
EOF
chmod 0644 /etc/cron.d/onetwoboard-expire
cron

echo "=== Применяем миграции ==="
python manage.py migrate --noinput

echo "=== Собираем статику ==="
# Убираем symlink static -> staticfiles, иначе collectstatic зациклится
if [ -L /app/static ]; then
    rm -f /app/static
fi
python manage.py collectstatic --noinput

echo "=== Ссылка static -> staticfiles ==="
if [ -e /app/static ] && [ ! -L /app/static ]; then
    rm -rf /app/static
fi
ln -sfn /app/staticfiles /app/static

echo "=== Запускаем Gunicorn ==="
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
