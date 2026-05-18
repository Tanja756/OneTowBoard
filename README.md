# OneTwoBoard — доска объявлений на Django

[English](README_EN.md)

Современная доска объявлений с модерацией, иерархическими категориями, динамическими параметрами и адаптивным интерфейсом. Проект готов к развёртыванию в Docker с HTTPS через Nginx.

**Демо:** [gripol.online](https://gripol.online)

## Стек технологий

- **Python 3.13+**
- **Django 5.2 (LTS)**
- **SQLite** (легко заменить на PostgreSQL)
- **Bootstrap 5.3** (CDN)
- **Pillow** — обработка изображений
- **django-allauth** — вход через Google (опционально)
- **Gunicorn** + **WhiteNoise** — продакшен
- **Docker** — контейнеризация

## Основные возможности

### Пользователи

- Регистрация с выбором типа аккаунта: **частное лицо** / **компания**
- **Вход через Google** (опционально, `ENABLE_GOOGLE_AUTH`); после входа запрашиваются недостающие данные (телефон, город, отображаемое имя)
- Отображаемое имя (если не задано — логин)
- **Смена пароля** и **восстановление пароля** по email
- **Верификация email** при регистрации
- Личный кабинет: профиль, аватар, контакты, смена типа аккаунта
- Раздел «Мои объявления»: редактирование, удаление, завершение
- **Обязательный телефон** с маской `+7 (999) 999-99-99` (валидация на сервере)

### Объявления

- Несколько фото при публикации (главное определяется автоматически)
- Модерация: статус «На модерации» до одобрения администратором
- **Срок действия** (1 сутки — 1 месяц); просроченные завершаются командой `expire_listings` (cron)
- Динамические параметры категории (AJAX), обязательны перед публикацией
- **Внешний ID** (`external_id`) — уникальный идентификатор объявления (UUID); используется при массовом импорте для создания и обновления записей
- **Контактный телефон объявления** (`contact_phone`) — отдельный номер для конкретного объявления; в админке и на странице объявления имеет приоритет над телефоном профиля автора
- Детальная страница: галерея со слайдером (мышь и клавиатура), цена с форматированием (`15 000 ₽`), просмотры за сегодня и всего, дата окончания публикации
- Контакты видны только **авторизованным** пользователям; телефон скрыт до нажатия «Показать телефон», отображается в формате `+7 (999) 999-99-99`
- Уникальный подсчёт просмотров для авторизованных пользователей (раз в сутки)
- В списках и «Моих объявлениях»: относительная дата («Сегодня», «Вчера», «N дней назад»), остаток срока («Осталось N дн.» / «Истекло»)
- Редактирование, удаление фото, **завершение** объявления автором
- Безопасные имена файлов (UUID), сжатие до 850 px по большей стороне

### Категории и поиск

- Иерархическое дерево категорий с наследованием параметров
- Фильтрация по параметрам, цене, полнотекстовый поиск
- Сортировка по дате и цене, пагинация с сохранением фильтров
- Два режима списка: плитки и строки

### Продвижение (через админку)

- **Закрепление** (`is_sticky`), **срочность** (`is_urgent`), **выделение** (`is_promoted`)
- Панель «Рекомендуемые» под деревом категорий

### Почта и уведомления

- SMTP через переменные окружения (в разработке — консольный бэкенд)
- Уведомления техподдержке о новых пользователях и объявлениях (`NOTIFY_ADMIN_NEW_USER`, `NOTIFY_ADMIN_NEW_LISTING`)

### Админка и безопасность

- Массовые действия с объявлениями (одобрить, деактивировать, на модерацию), предпросмотр изображений
- Поиск объявлений по заголовку, описанию, автору, **внешнему ID** и **контактному телефону**
- В профилях пользователей отображается статус **верификации email**
- CSRF, валидация отображаемого имени, защита от дублирования форм (одноразовый токен)

## Быстрый старт (локально)

```bash
git clone https://github.com/Tanja756/OneTowBoard.git
cd OneTowBoard
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/

Доступ с других устройств в локальной сети:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Docker (продакшен)

Сборка:

```bash
docker build -t onetwoboard .
```

Запуск — достаточно передать **`.env`**, каталог для **БД** и каталог для **media**:

```bash
mkdir -p ./data/db ./data/media

docker run -d \
  --name onetwoboard \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/data/db:/data/db" \
  -v "$(pwd)/data/media:/data/media" \
  onetwoboard

docker exec -it onetwoboard python manage.py createsuperuser
```

### Что происходит внутри контейнера

| Путь | Назначение |
|------|------------|
| `/data/db/db.sqlite3` | База SQLite (том с хоста) |
| `/data/media/` | Загруженные файлы (том с хоста) |
| `/app/staticfiles/` | Собранная статика (`collectstatic`) |
| `/app/static` | Символическая ссылка на `staticfiles` (для Nginx и единого пути) |

По умолчанию: часовой пояс **Europe/Moscow (UTC+3)**, WhiteNoise отдаёт статику через Gunicorn.

`expire_listings` по cron **ежедневно в 03:00** — расписание в `.env`: `CRON_EXPIRE_SCHEDULE=0 3 * * *`.

Ручной запуск:

```bash
docker exec onetwoboard python manage.py expire_listings
```

## Nginx (пример HTTPS)

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    client_max_body_size 20M;

    # В контейнере: /app/static -> staticfiles (symlink)
    location /static/ {
        alias /path/to/app/static/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias /path/to/data/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Переменные окружения (`.env`)

Создайте файл `.env` в корне проекта:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

# Сайт (SEO, шапка, футер)
SITE_NAME=OneTwoBoard
SITE_DESCRIPTION=Бесплатная доска объявлений
SITE_KEYWORDS=доска объявлений, купить, продать

# Google OAuth (опционально)
ENABLE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Почта
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com
TECH_SUPPORT_EMAIL=support@example.com

# Уведомления техподдержке
NOTIFY_ADMIN_NEW_USER=False
NOTIFY_ADMIN_NEW_LISTING=False

# Docker (опционально)
TZ=Europe/Moscow
CRON_EXPIRE_SCHEDULE=0 3 * * *
# DJANGO_DB_DIR=/data/db
# DJANGO_MEDIA_ROOT=/data/media
```

## Cron (без Docker)

Ежедневная проверка просроченных объявлений (пример — в 03:00):

```cron
0 3 * * * cd /path/to/OneTowBoard && /path/to/venv/bin/python manage.py expire_listings >> /var/log/onetwoboard_expire.log 2>&1
```

## Команды управления

| Команда | Описание |
|---------|----------|
| `python manage.py expire_listings` | Завершить объявления с истёкшим сроком |
| `python manage.py import_listings <dir>` | Массовый импорт/обновление объявлений из папок |

### Импорт объявлений (`import_listings`)

Каждая подпапка в `<dir>` — одно объявление; имя папки становится `external_id`. При повторном запуске существующие записи **обновляются** по этому ID.

Структура папки:

```
12345/                    # external_id
├── title.txt             # обязательно; префикс «№868137 - » удаляется автоматически
├── description.txt       # необязательно
├── price.txt             # необязательно; из строки извлекается число
├── phone.txt             # контактный телефон объявления
├── category.txt          # slug категории
├── params.json           # параметры категории (JSON)
├── *.jpg / *.png         # фотографии (файлы phone.* игнорируются)
```

Импортированные объявления получают статус `active`, срок **7 дней** и случайную дату публикации за вчерашний день. Автор — первый суперпользователь в базе.

```bash
python manage.py import_listings /path/to/data
python manage.py import_listings /path/to/data --category electronics
python manage.py import_listings /path/to/data --param deal_type sale --param condition used
```

## Первые шаги после установки

1. Войдите в админку и создайте категории (при необходимости — подкатегории и параметры).
2. Зарегистрируйте тестового пользователя и подайте объявление.
3. Одобрите объявление в админке.
4. Настройте cron или используйте Docker с встроенным cron.

## Структура проекта

```
OneTwoBoard/
├── config/                 # settings, urls, wsgi, middleware
├── apps/
│   ├── users/              # пользователи, профили, OAuth
│   ├── listings/           # объявления, изображения, просмотры
│   ├── categories/         # категории и параметры
│   ├── search/             # поиск и фильтрация
│   └── ratings/            # заготовка для оценок
├── templates/
├── static/
├── media/
├── db/                     # SQLite (продакшен)
├── manage.py
├── requirements.txt
├── scripts/run_expire.sh   # cron: expire_listings
├── Dockerfile
├── entrypoint.sh
├── README.md
└── README_EN.md
```

## Планы развития

- Избранное (закладки)
- Личные сообщения между пользователями
- Рейтинги и отзывы
- Расширенные email-уведомления
- Полнотекстовый поиск (PostgreSQL)
- Рекламные баннеры

## Лицензия

[MIT](LICENSE)
