FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Moscow \
    DJANGO_DB_DIR=/data/db \
    DJANGO_MEDIA_ROOT=/data/media \
    DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev libjpeg-dev zlib1g-dev cron tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo "$TZ" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Убираем хостовый symlink static; после collectstatic entrypoint создаст static -> staticfiles
RUN rm -f /app/static \
    && mkdir -p /data/db /data/media /app/staticfiles /var/log /etc/onetwoboard \
    && chmod +x entrypoint.sh scripts/run_expire.sh

VOLUME ["/data/db", "/data/media"]

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
