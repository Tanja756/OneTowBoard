FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev libjpeg-dev zlib1g-dev cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/db /app/media /app/staticfiles /var/log \
    && chmod 777 /var/log

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]