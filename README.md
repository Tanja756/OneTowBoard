# OneTwoBoard — доска объявлений на Django

[English](README_EN.md)

Современная доска объявлений: модерация, иерархические категории, динамические параметры, продвижение объявлений, **адаптивный интерфейс с раздельными шаблонами для ПК и мобильных** на Bootstrap 5. Готова к запуску в **Docker** (SQLite, media на томах, cron, Nginx).

**Демо:** [gripol.online](https://gripol.online)

## Стек технологий

| Компонент | Назначение |
|-----------|------------|
| Python 3.13+ | Язык |
| Django 5.2 (LTS) | Backend |
| SQLite | БД (легко заменить на PostgreSQL) |
| Bootstrap 5.3 | UI (CDN) |
| Pillow | Изображения, сжатие до 850 px |
| django-allauth + cryptography | Вход через Google (опционально) |
| django-user-agents | Определение устройства (ПК/мобильный) |
| Gunicorn + WhiteNoise | Продакшен |
| Docker + cron | Контейнер, автозавершение просроченных объявлений |

## Основные возможности

### Пользователи

- Регистрация: **частное лицо** / **компания**
- **Google OAuth** (`ENABLE_GOOGLE_AUTH`) — дозаполнение профиля (телефон, город, имя)
- Email: верификация, смена и восстановление пароля
- Личный кабинет: аватар, контакты, тип аккаунта, **«Мои объявления»**
- Телефон в профиле обязателен, маска `+7 (999) 999-99-99`, проверка на сервере

### Объявления

- Несколько фото, главное выбирается автоматически
- Модерация (`moderation` → `active`), срок публикации 1 сутки — 1 месяц
- `expire_listings` — автозавершение просроченных (cron в Docker или на хосте)
- `external_id` — уникальный ID; импорт и обновление пакетами
- `contact_phone` — телефон объявления (приоритет над телефоном автора)
- Галерея со слайдером; цена `15 000 ₽`; просмотры (уникально, 1 раз в сутки для авторизованных)
- Контакты только для вошедших пользователей; «Показать телефон»
- Завершение, редактирование, удаление фото; UUID-имена файлов

### Категории и поиск

- Дерево категорий, наследование параметров, изображение-заглушка
- Типы параметров: список, да/нет, число, текст, **поле с маской**
- Фильтры по параметрам и цене, поиск по заголовку и описанию
- Сортировка, пагинация; виды **плитки** / **список**

### Продвижение (админка)

- `is_sticky`, `is_urgent`, `is_promoted`
- Блок «Рекомендуемые» на главной и в категориях

### Почта

- SMTP через `.env` (локально — консольный бэкенд)
- Уведомления техподдержке: `NOTIFY_ADMIN_NEW_USER`, `NOTIFY_ADMIN_NEW_LISTING`

### Избранное

- Сохранение объявлений в **избранное** одним кликом (AJAX)
- Страница **«Избранные объявления»** в личном кабинете
- Индикация избранного на карточках (главная, категории, поиск)
- Завершённые объявления отображаются блеклыми с пометкой
- Номер телефона отсутствует в HTML — загружается как изображение с сервера (защита от парсинга)
- Можно отключить через `ENABLE_FAVORITES=False` в `.env`

### Адаптивный интерфейс

- **Автоматическое определение устройства** через `django_user_agents` — ПК или мобильный
- Функция `get_device_template(request, template_name)` в `apps/utils.py` выбирает шаблон из `desktop/` или `mobile/`
- **Десктоп**: полная шапка с логотипом, поиском (с категориями), кнопкой «+ Новое объявление», меню пользователя, боковая панель с деревом категорий и блоком «Рекомендуемые», подвал
- **Мобильный**: компактная шапка, поиск на всю ширину, нижняя навигационная панель (Главная, Поиск, Добавить, Избранное, Профиль), модальное окно выбора категории с пошаговым деревом, `padding-bottom: 70px` в CSS
- Общие компоненты (`includes/filter_sort.html`, `ratings/star_rating.html`) вынесены в `templates/` и используются обеими версиями

### Безопасность

- CSRF, валидация отображаемого имени, одноразовый токен форм
- Номер телефона не отображается в HTML — генерируется как PNG-изображение на лету

### SEO и индексация

- В заголовок страницы объявления (`<title>`) автоматически добавляется **город автора**, если он указан. Это повышает видимость в локальной выдаче (например, «Продам велосипед в Григорополисской»)
- Мета-описание (`description`) страницы объявления также учитывает город
- Карта сайта **`/sitemap.xml`** генерируется автоматически (Django sitemaps) и содержит:
  - все **активные** незавершённые объявления (`changefreq: daily`)
  - все **категории** (`changefreq: weekly`)
  - **главную** страницу (`changefreq: weekly`, приоритет 1.0)
- Sitemap готов к отправке в [Google Search Console](https://search.google.com/search-console) и [Яндекс.Вебмастер](https://webmaster.yandex.ru/) сразу после деплоя

## Быстрый старт (локально)

```bash
git clone https://github.com/Tanja756/OneTowBoard.git
cd OneTowBoard
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/

## Docker (продакшен)
###https://hub.docker.com/u/sergvuntyped

```bash
docker build -t onetwoboard .

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

При старте контейнера автоматически: миграции, `collectstatic`, симлинк **`/app/static` → `staticfiles`**, cron, Gunicorn.

| Путь в контейнере | Назначение |
|-------------------|------------|
| `/data/db/db.sqlite3` | База (том с хоста) |
| `/data/media/` | Загрузки (том с хоста) |
| `/app/staticfiles/` | Собранная статика |
| `/app/static` | Symlink на `staticfiles` (для Nginx) |

Часовой пояс по умолчанию: **Europe/Moscow (UTC+3)**.  
`expire_listings` — **ежедневно в 03:00** (`CRON_EXPIRE_SCHEDULE` в `.env`).

```bash
docker exec onetwoboard python manage.py expire_listings   # вручную
```

## Nginx (пример)

Статику и media можно отдавать с хоста, смонтировав тома контейнера или каталоги напрямую:

```nginx
location /static/ {
    alias /path/to/app/static/;   # symlink -> staticfiles
    expires 30d;
}
location /media/ {
    alias /path/to/data/media/;
    expires 30d;
}
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Переменные окружения (`.env`)

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

SITE_NAME=OneTwoBoard
SITE_DESCRIPTION=Бесплатная доска объявлений
SITE_KEYWORDS=доска объявлений, купить, продать

ENABLE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Избранное (включено по умолчанию)
ENABLE_FAVORITES=True

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@example.com
TECH_SUPPORT_EMAIL=support@example.com

NOTIFY_ADMIN_NEW_USER=False
NOTIFY_ADMIN_NEW_LISTING=False

# Docker
TZ=Europe/Moscow
CRON_EXPIRE_SCHEDULE=0 3 * * *
```

Подробная настройка Google — в разделе [Вход через Google](#вход-через-google-oauth-20) ниже.

## Вход через Google (OAuth 2.0)

### Включение

Google-авторизация управляется флагом `ENABLE_GOOGLE_AUTH` в `.env`:

```env
ENABLE_GOOGLE_AUTH=True
```

### Настройка

1. **Создайте проект** в [Google Cloud Console](https://console.cloud.google.com/) (новый или существующий).

2. **Экран согласия OAuth** (APIs & Services → OAuth consent screen):
   - тип **External**;
   - заполните название приложения, email поддержки, логотип;
   - в разрешённые домены добавьте ваш домен (например, `gripol.online`) и `localhost`.

3. **OAuth 2.0 Client ID** (Credentials → Create Credentials → OAuth client ID):
   - тип приложения: **Web application**;
   - **Authorized redirect URIs**:
     - `https://ваш-домен/accounts/google/login/callback/`
     - `http://127.0.0.1:8000/accounts/google/login/callback/` (локальная разработка)
   - сохраните **Client ID** и **Client Secret**.

4. **Переменные в `.env`:**

```env
ENABLE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=ваш-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=ваш-client-secret
SITE_ID=1
```

5. **Сайт и социальное приложение в админке** (`/admin/`):
   - **Sites** — сайт с доменом проекта (например, `gripol.online`);
   - **Social applications** — провайдер **Google**, Client ID и Secret из Cloud Console, привязка к созданному сайту.

6. **Перезапустите** сервер или контейнер. На страницах входа и регистрации появятся кнопки «Войти через Google» / «Зарегистрироваться через Google».

### Отключение

```env
ENABLE_GOOGLE_AUTH=False
```

Перезапустите приложение. Кнопки Google исчезнут, django-allauth отключится.

### Важно

- При первом входе через Google нужно заполнить **отображаемое имя**, **телефон** и **город** (если не были указаны ранее) — без этого сайт не даст продолжить работу.
- Связывание аккаунтов по email происходит автоматически.
- CSRF и сессии работают в штатном режиме.

## Команды управления

| Команда | Описание |
|---------|----------|
| `expire_listings` | Завершить объявления с истёкшим `expiry_date` |
| `import_listings <dir>` | Импорт/обновление по папкам (`external_id` = имя папки) |
| `reset_sequences` | Сброс автоинкремента ID в БД (после ручного импорта) |

**Структура папки импорта:**

```
12345/
├── title.txt          # обязательно
├── description.txt
├── price.txt
├── phone.txt          # contact_phone
├── category.txt       # slug категории
├── params.json
└── *.jpg
```

```bash
python manage.py import_listings ./data --category electronics
python manage.py import_listings ./data --param deal_type sale
```

## Структура проекта

```
OneTwoBoard/
├── config/                 # settings, urls, sitemaps, middleware, context_processors
├── apps/
│   ├── users/              # профили, OAuth, регистрация
│   ├── listings/           # объявления, фото, просмотры, импорт/expire
│   ├── categories/         # дерево категорий, параметры, фильтры
│   ├── search/             # поиск и сортировка
│   └── ratings/            # рейтинги и отзывы (в разработке)
├── templates/
│   ├── base.html                 # корневой базовый шаблон (для allauth, email)
│   ├── desktop/                  # шаблоны для ПК
│   │   ├── base.html
│   │   ├── listings/
│   │   ├── categories/
│   │   ├── search/
│   │   └── users/
│   ├── mobile/                   # шаблоны для мобильных
│   │   ├── base.html
│   │   ├── listings/
│   │   ├── categories/
│   │   ├── search/
│   │   └── users/
│   ├── includes/                 # общие компоненты (filter_sort.html)
│   ├── ratings/                  # общие компоненты (star_rating.html)
│   └── categories/
│       └── parameters_form.html  # AJAX-рендер параметров
├── static/                 # CSS, favicon
├── staticfiles/            # собранная статика (генерируется collectstatic)
├── media/                  # пользовательские загрузки
├── db/                     # SQLite (продакшен)
├── scripts/run_expire.sh   # обёртка для cron
├── Dockerfile
├── entrypoint.sh
└── manage.py
```

## В разработке

- **Личные сообщения**

## Планы

- Рейтинги и отзывы (`apps/ratings`)
- Расширенные email-уведомления
- Полнотекстовый поиск (PostgreSQL)
- Рекламные баннеры

## Лицензия

[MIT](LICENSE)
