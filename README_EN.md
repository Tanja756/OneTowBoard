# OneTwoBoard — Classifieds Board on Django

A modern classifieds board with moderation, hierarchical categories, dynamic parameters and a responsive interface.  
The project is fully ready for deployment in Docker with HTTPS via Nginx.

### Демо
https://gripol.online

## Tech Stack

- **Python 3.13+**
- **Django 5.2 (LTS)**
- **SQLite** (easy to replace with PostgreSQL)
- **Bootstrap 5.3** (CDN)
- **Pillow** (image processing)
- **Gunicorn** + **WhiteNoise** (production)
- **Docker** (containerization)

## Key Features

### Users
- Registration with account type selection: **Individual** / **Company**
- Display name (if not set, login is used)
- **Password change** via personal account
- Personal account: profile settings, avatar, contacts, account type change
- "My listings" section with management (edit, delete, complete)
- **Mandatory phone number** with input mask `+7 (999) 999-99-99` (server-side validation)

### Listings
- Creation with multiple photo upload (main image determined automatically)
- Moderation: a new listing gets "Pending moderation" status, visible only to author and admin; after approval it becomes available to everyone
- **Duration**: user selects duration (1 day, 1 week, 2 weeks, 1 month, 1 month by default); expired listings are automatically completed (via cron command)
- Dynamic parameters depending on selected category (via AJAX)
- Mandatory category parameters before publishing
- Detail page: gallery with modal slider (mouse and keyboard navigation), price, views, contacts (phone hidden until "Show phone" click), author city
- **View counting**: unique authorized user counted once per day (anonymous not counted)
- Edit and delete listings by author or admin
- Ability to delete previously uploaded photos and add new ones while editing
- **Listing completion**: author can mark listing as completed; it disappears from common listings but remains accessible via direct link and in personal account
- Secure file upload: names generated based on UUID, avoiding Cyrillic issues
- **Image compression**: all uploaded photos and avatars automatically reduced to 850 px on the long side (keeping proportions)
- Notification after publishing: "Listing submitted for moderation. It will appear in the feed after approval by a moderator."

### Categories and Parameters
- Hierarchical category tree (nesting via parent relationship)
- Interactive category tree when creating listing (accordion, cannot select parent category)
- Custom parameters for each category (type: select from list or yes/no)
- Inheritance of parameters from parent categories (child gets all ancestor parameters)
- Filtering listings by parameters on category page
- When selecting parent category, listings from it and all subcategories are shown
- Categories can have their own image, used as placeholder for listings without photos (walking up the parent hierarchy)

### Search and Filters
- Full-text search by title and description (case-insensitive)
- Price filter (from/to)
- Sorting: by date (newest/oldest) and by price (cheapest/most expensive)
- Compact drop-down filter panels in DNS‑shop style
- Pagination preserving filter and sort parameters
- Expired listings automatically excluded from results

### Listing Promotion (via admin, later by users)
- **Sticky** (`is_sticky`): always at the top
- **Urgent** (`is_urgent`): red "Urgent" badge, urgent listed after sticky
- **Highlight** (`is_promoted`): yellow background and orange left border on the card
- **"Recommended" panel** under categories tree (random promoted listings + ordinary)

### Interface
- Fully responsive design with Bootstrap 5
- Equal height listing cards
- Breadcrumbs on detail page
- Modal photo viewer with slide ability
- Mobile version with optimized header ("New listing" button centered)
- When creating listing, category and main fields placed left/right on large screens
- Recommended panel hidden on mobile devices

### SEO
- Unique titles and meta descriptions for all pages
- Site name, description and keywords set in settings and used in templates
- Human-readable URLs (slug for categories)
- `favicon.ico` file linked from static

### Admin Panel
- Manage categories, parameters, listings, images, users
- Bulk actions: approve, deactivate, send to moderation
- Preview of images and avatars
- Customized headers and styles
- Fields `is_promoted`, `is_sticky`, `is_urgent`, `is_completed`, `expiry_date` available in list and filters

### Security
- CSRF protection with trusted origins configured for production
- Display name validation (email and phone numbers disallowed)
- Mandatory CSRF token check for all POST forms
- Long title overflow protection (`word-break`, `overflow-wrap`)

## Quick Start (Local)

    bash
    git clone https://github.com/Tanja756/OneTowBoard.git
    cd OneTowBoard
    python3 -m venv venv
    source venv/bin/activate      # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python3 manage.py migrate
    python3 manage.py createsuperuser
    python3 manage.py runserver

    Open in browser:
        Main site: http://127.0.0.1:8000
        Admin panel: http://127.0.0.1:8000/admin/
    To access from other devices on local network:
    python3 manage.py runserver 0.0.0.0:8000

### Docker Deployment (Production)
    docker build -t onetwoboard .
    docker run -d \
        --name onetwoboard \
        -p 8000:8000 \
        -v /путь/к/db:/app/db \
        -v /путь/к/media:/app/media \
        -v /путь/к/static:/app/staticfiles \
        --env-file .env \
        onetwoboard
    docker exec -it onetwoboard python manage.py createsuperuser

### Nginx Configuration (HTTPS example)
    server {
        listen 80;
        server_name your-domain.ru;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 443 ssl;
        server_name your-domain.ru;
    
        ssl_certificate /etc/letsencrypt/live/your-domain.ru/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.ru/privkey.pem;
    
        client_max_body_size 20M;
    
        location /static/ {
            alias /path/to/staticfiles/;
            expires 30d;
            add_header Cache-Control "public";
        }
    
        location /media/ {
            alias /path/to/media/;
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

### Environment Variables (.env)
    DJANGO_SECRET_KEY=your-reliable-secret-key
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=your-domain.ru,www.your-domain.ru
    DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.ru,https://www.your-domain.ru


### Project Structure
    OneTwoBoard/
    ├── config/                    # Django settings (settings, urls, wsgi, asgi)
    ├── apps/
    │   ├── users/                 # Users and profiles
    │   ├── listings/              # Listings, images, ViewLog model
    │   ├── categories/            # Categories, parameters, template tags
    │   ├── search/                # Search and filtering
    │   └── ratings/               # Placeholder for future ratings
    ├── templates/                 # HTML templates (includes and subfolders)
    ├── static/                    # Static files (CSS, images, favicon.ico)
    ├── media/                     # User-uploaded files (avatars, photos)
    ├── db/                        # SQLite database file (production)
    ├── manage.py
    ├── requirements.txt
    ├── Dockerfile
    ├── entrypoint.sh
    ├── crontab.txt
    ├── .env.example
    └── README.md

### Future Plans
    Favorites (bookmarks)
    Private messaging between sellers and buyers
    Ratings and reviews
    Email notifications
    Full-text search (when migrating to PostgreSQL)
    Advertising banners