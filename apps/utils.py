import uuid
import os
from django.conf import settings
import logging
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

logger = logging.getLogger(__name__)

# Debug-логгер (включается через ENABLE_DEBUG_LOGGING=True в .env)
debug_logger = logging.getLogger('debug')

def log_debug(msg, *args, **kwargs):
    """Логирует сообщение только если расширенное логирование включено."""
    if settings.ENABLE_DEBUG_LOGGING:
        debug_logger.debug(msg, *args, **kwargs)

def safe_upload_to(instance, filename, subfolder):
    """Генерирует уникальное имя: <subfolder>/<uuid>.<ext>"""
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(subfolder, new_name)

def avatar_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'avatars')

def listing_image_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'listings')

def compress_uploaded_image(uploaded_file, max_size=(800, 800), quality=85):
    """
    Сжимает загруженное изображение, уменьшая его до max_size и сохраняя в JPEG.
    Возвращает InMemoryUploadedFile.
    """
    try:
        img = Image.open(uploaded_file)
    except UnidentifiedImageError:
        logger.warning(f"Не удалось распознать изображение: {uploaded_file.name}")
        return uploaded_file

    # Конвертируем в RGB, если нужно
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')

    # Уменьшаем размер
    img.thumbnail(max_size, Image.LANCZOS)

    # Сохраняем в BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality)
    output.seek(0)

    # Возвращаем как InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{uploaded_file.name.rsplit('.', 1)[0]}.jpg",
        'image/jpeg',
        sys.getsizeof(output),
        None
    )

def category_image_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'categories')

def generate_thumbnail(image_instance, width=400, height=300):
    from django.conf import settings
    if not image_instance.image:
        log_debug("generate_thumbnail: нет изображения для %s", image_instance)
        return None
    original_path = image_instance.image.path
    thumb_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
    base_name = os.path.basename(original_path)
    thumb_name = f'{os.path.splitext(base_name)[0]}_thumb.jpg'
    thumb_path = os.path.join(thumb_dir, thumb_name)
    if os.path.exists(thumb_path):
        log_debug("generate_thumbnail: миниатюра уже существует — %s", thumb_name)
        return os.path.join('thumbnails', thumb_name)
    os.makedirs(thumb_dir, exist_ok=True)
    try:
        img = Image.open(original_path)
        original_size = img.size
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.thumbnail((width, height), Image.LANCZOS)
        img.save(thumb_path, format='JPEG', quality=80, optimize=True)
        log_debug("generate_thumbnail: %s %dx%d -> %dx%d", base_name, original_size[0], original_size[1], img.width, img.height)
    except Exception as e:
        logger.error(f'Ошибка создания миниатюры для {original_path}: {e}')
        return None
    return os.path.join('thumbnails', thumb_name)

def get_device_template(request, template_name: str) -> str:
    """
    Возвращает путь к шаблону в зависимости от устройства.
    Для мобильных - mobile/..., для десктопа - desktop/...
    """
    if hasattr(request, 'user_agent') and request.user_agent.is_mobile:
        return f'mobile/{template_name}'
    return f'desktop/{template_name}'