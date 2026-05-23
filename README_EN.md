# OneTwoBoard — Classifieds Board on Django

[Русский](README.md)

A modern classifieds board with moderation, hierarchical categories, dynamic parameters, and a **responsive interface with separate templates for desktop and mobile** on Bootstrap 5. Ready for Docker deployment with HTTPS via Nginx.

**Demo:** [gripol.online](https://gripol.online)

## Tech Stack

- **Python 3.13+**
- **Django 5.2 (LTS)**
- **SQLite** (easy to replace with PostgreSQL)
- **Bootstrap 5.3** (CDN)
- **Pillow** — image processing
- **django-allauth** — optional Google sign-in
- **django-user-agents** — device detection (desktop/mobile)
- **Gunicorn** + **WhiteNoise** — production
- **Docker** — containerization

## Key Features

### Users

- Registration with account type: **individual** / **company**
- **Google sign-in** (optional, `ENABLE_GOOGLE_AUTH`); missing profile fields requested after login
- Display name (falls back to username)
- **Password change** and **password reset** via email
- **Email verification** on registration
- Personal account: profile, avatar, contacts, account type
- **My listings**: edit, delete, mark as completed
- **Required phone** with mask `+7 (999) 999-99-99` (server-side validation)

### Listings

- Multiple photos per listing (main image selected automatically)
- Moderation: **pending** until admin approval
- **Expiry duration** (1 day – 1 month); expired listings completed by `expire_listings` (cron)
- Dynamic category parameters (AJAX), required before publish
- **External ID** (`external_id`) — unique listing identifier (UUID); used for bulk import create/update
- **Listing contact phone** (`contact_phone`) — per-listing phone number; takes priority over the author's profile phone
- Detail page: gallery with slider (mouse and keyboard), formatted price (`15 000 ₽`), views today and total, expiry date
- Contacts visible only to **authenticated** users; phone hidden until "Show phone" is clicked, displayed as `+7 (999) 999-99-99`
- Unique view counting for authenticated users (once per day)
- In listings and "My listings": relative dates ("Today", "Yesterday", "N days ago"), time left ("N days left" / "Expired")
- Edit, remove photos, **complete** listing as author
- Safe filenames (UUID), compression to 850 px on the long edge

### Categories & Search

- Hierarchical categories with inherited parameters
- Filter by parameters and price, full-text search
- Sort by date and price, pagination preserving filters
- Grid and list view modes

### Promotion (admin)

- **Sticky** (`is_sticky`), **urgent** (`is_urgent`), **highlight** (`is_promoted`)
- **Recommended** panel under the category tree

### Email & Notifications

- SMTP via environment variables (console backend in development)
- Optional support notifications (`NOTIFY_ADMIN_NEW_USER`, `NOTIFY_ADMIN_NEW_LISTING`)

### Favorites

- **Save listings** to favorites with one click (AJAX)
- **Favorites page** in the personal account
- Favorite indicator on listing cards (homepage, categories, search)
- Completed listings shown faded with a badge
- Phone number is not in HTML — loaded as a server-generated image (anti-scraping)
- Can be disabled via `ENABLE_FAVORITES=False` in `.env`

### Responsive Interface

- **Automatic device detection** via `django_user_agents` — desktop or mobile
- `get_device_template(request, template_name)` in [`apps/utils.py`](apps/utils.py:95) selects the appropriate template from `desktop/` or `mobile/`
- **Desktop**: full header with logo, search bar (with category dropdown), "+ New listing" button, user dropdown menu, sidebar with category tree and recommended panel, footer
- **Mobile**: compact header, full-width search bar, **bottom navigation bar** (Home, Search, Add, Favorites, Profile), category selection modal with JS-driven step-by-step tree, `padding-bottom: 70px` in CSS for bottom nav clearance
- Shared components (`includes/filter_sort.html`, `ratings/star_rating.html`) are placed in the root `templates/` directory and used by both versions

### Admin & Security

- Bulk listing actions (approve, deactivate, send to moderation), image previews
- Search listings by title, description, author, **external ID**, and **contact phone**
- User profiles show **email verification** status
- CSRF protection, display name validation, duplicate form protection (one-time token)
- Phone number never appears in HTML — dynamically generated as a PNG image

### SEO & Indexing

- The listing page `<title>` automatically includes the **author's city** when set — better local search visibility (e.g. "Bike for sale in Grigoropolisskaya")
- The listing meta `description` also includes the city when available
- **`/sitemap.xml`** is generated automatically (Django sitemaps) and includes:
  - all **active**, non-completed listings (`changefreq: daily`)
  - all **categories** (`changefreq: weekly`)
  - the **home** page (`changefreq: weekly`, priority 1.0)
- Ready to submit to [Google Search Console](https://search.google.com/search-console) and [Yandex Webmaster](https://webmaster.yandex.ru/) right after deploy

## Quick Start (Local)

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

- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

Access from other devices on the local network:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Docker (Production)

Build:

```bash
docker build -t onetwoboard .
```

Run — only **`.env`**, a **database** directory, and a **media** directory are required:

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

### Inside the container

| Path | Purpose |
|------|---------|
| `/data/db/db.sqlite3` | SQLite database (host volume) |
| `/data/media/` | User uploads (host volume) |
| `/app/staticfiles/` | Collected static files (`collectstatic`) |
| `/app/static` | Symlink to `staticfiles` (for Nginx and a single path) |

Defaults: timezone **Europe/Moscow (UTC+3)**; WhiteNoise serves static files via Gunicorn.

`expire_listings` runs via cron **daily at 03:00** — set `CRON_EXPIRE_SCHEDULE=0 3 * * *` in `.env`.

Manual run:

```bash
docker exec onetwoboard python manage.py expire_listings
```

## Nginx (HTTPS Example)

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

    # In container: /app/static -> staticfiles (symlink)
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

## Environment Variables (`.env`)

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

# Site (SEO, header, footer)
SITE_NAME=OneTwoBoard
SITE_DESCRIPTION=Free classifieds board
SITE_KEYWORDS=classifieds, buy, sell

# Google OAuth (optional)
ENABLE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Favorites (enabled by default)
ENABLE_FAVORITES=True

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com
TECH_SUPPORT_EMAIL=support@example.com

# Support notifications
NOTIFY_ADMIN_NEW_USER=False
NOTIFY_ADMIN_NEW_LISTING=False

# Docker (optional)
TZ=Europe/Moscow
CRON_EXPIRE_SCHEDULE=0 3 * * *
# DJANGO_DB_DIR=/data/db
# DJANGO_MEDIA_ROOT=/data/media
```

See [Sign in with Google](#sign-in-with-google-oauth-20) below for full OAuth setup.

## Sign in with Google (OAuth 2.0)

### Enabling

Google sign-in is controlled by `ENABLE_GOOGLE_AUTH` in `.env`:

```env
ENABLE_GOOGLE_AUTH=True
```

### Setup

1. **Create a project** in [Google Cloud Console](https://console.cloud.google.com/).

2. **OAuth consent screen** (APIs & Services → OAuth consent screen):
   - choose **External**;
   - fill in app name, support email, logo;
   - add your domain (e.g. `gripol.online`) and `localhost` to authorized domains.

3. **OAuth 2.0 Client ID** (Credentials → Create Credentials → OAuth client ID):
   - application type: **Web application**;
   - **Authorized redirect URIs**:
     - `https://your-domain/accounts/google/login/callback/`
     - `http://127.0.0.1:8000/accounts/google/login/callback/` (local development)
   - save **Client ID** and **Client Secret**.

4. **`.env` variables:**

```env
ENABLE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SITE_ID=1
```

5. **Admin panel** (`/admin/`):
   - **Sites** — add your domain (e.g. `gripol.online`);
   - **Social applications** — provider **Google**, Client ID and Secret from Cloud Console, link to the site.

6. **Restart** the server or container. "Sign in with Google" buttons appear on login and registration pages.

### Disabling

```env
ENABLE_GOOGLE_AUTH=False
```

Restart the app. Google buttons disappear and django-allauth is fully disabled.

### Notes

- On first Google sign-in, users must complete **display name**, **phone**, and **city** if missing — otherwise the site blocks further use.
- Accounts are linked by email automatically.
- CSRF and sessions work as usual.

## Cron (without Docker)

Daily expiry check (example at 03:00):

```cron
0 3 * * * cd /path/to/OneTowBoard && /path/to/venv/bin/python manage.py expire_listings >> /var/log/onetwoboard_expire.log 2>&1
```

## Management Commands

| Command | Description |
|---------|----------|
| `python manage.py expire_listings` | Complete listings past their expiry date |
| `python manage.py import_listings <dir>` | Bulk import/update listings from folders |
| `python manage.py reset_sequences` | Reset auto-increment IDs after manual DB imports |

### Import listings (`import_listings`)

Each subfolder in `<dir>` is one listing; the folder name becomes `external_id`. Re-running the command **updates** existing records by that ID.

Folder structure:

```
12345/                    # external_id
├── title.txt             # required; prefix like "№868137 - " is stripped automatically
├── description.txt       # optional
├── price.txt             # optional; first number is extracted
├── phone.txt             # listing contact phone
├── category.txt          # category slug
├── params.json           # category parameters (JSON)
├── *.jpg / *.png         # photos (files starting with phone.* are ignored)
```

Imported listings are set to `active`, **7-day** expiry, and a random publish time on yesterday. Author is the first superuser in the database.

```bash
python manage.py import_listings /path/to/data
python manage.py import_listings /path/to/data --category electronics
python manage.py import_listings /path/to/data --param deal_type sale --param condition used
```

## Getting Started

1. Log in to the admin panel and create categories (and parameters if needed).
2. Register a test user and submit a listing.
3. Approve the listing in the admin.
4. Set up cron or use Docker with built-in cron.

## Project Structure

```
OneTwoBoard/
├── config/                 # settings, urls, wsgi, middleware, context_processors
├── apps/
│   ├── users/              # users, profiles, OAuth, registration
│   ├── listings/           # listings, images, views, import/expire
│   ├── categories/         # categories, parameters, filtering
│   ├── search/             # search and sorting
│   └── ratings/            # ratings and reviews (in development)
├── templates/
│   ├── base.html                 # root base template (for allauth, email pages)
│   ├── desktop/                  # desktop-specific templates
│   │   ├── base.html
│   │   ├── listings/
│   │   ├── categories/
│   │   ├── search/
│   │   └── users/
│   ├── mobile/                   # mobile-specific templates
│   │   ├── base.html
│   │   ├── listings/
│   │   ├── categories/
│   │   ├── search/
│   │   └── users/
│   ├── includes/                 # shared components (filter_sort.html)
│   ├── ratings/                  # shared components (star_rating.html)
│   └── categories/
│       └── parameters_form.html  # AJAX parameter rendering
├── static/                 # CSS, favicon
├── staticfiles/            # collected static (generated by collectstatic)
├── media/                  # user uploads
├── db/                     # SQLite (production)
├── manage.py
├── requirements.txt
├── scripts/run_expire.sh   # cron wrapper for expire_listings
├── Dockerfile
├── entrypoint.sh
├── README.md
└── README_EN.md
```

## In Development

- **Private messages**

## Roadmap

- Ratings and reviews
- Extended email notifications
- Full-text search (PostgreSQL)
- Advertising banners

## License

[MIT](LICENSE)
