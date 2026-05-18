import uuid
import os
import logging
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

logger = logging.getLogger(__name__)

def safe_upload_to(instance, filename, subfolder):
    """Генерирует уникальное имя: <subfolder>/<uuid>.<ext>"""
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(subfolder, new_name)

def listing_image_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'listings')

def avatar_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'avatars')

def category_image_upload_to(instance, filename):
    return safe_upload_to(instance, filename, 'categories')

def compress_uploaded_image(image_field, max_dim=850):
    """
    Безопасно сжимает изображение. При ошибке оставляет оригинал.
    """
    try:
        img = Image.open(image_field.file)
        # Если формат не поддерживает прозрачность при сохранении в JPEG, конвертируем
        if img.mode in ('RGBA', 'LA', 'P') and img.format != 'GIF':
            if img.format != 'PNG':
                img = img.convert('RGB')
        width, height = img.size
        if max(width, height) <= max_dim:
            return  # не требуется сжатие

        # Вычисляем новые размеры с сохранением пропорций
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))

        img = img.resize((new_width, new_height), Image.LANCZOS)

        output = BytesIO()
        if img.mode == 'RGB':
            img.save(output, format='JPEG', quality=85, optimize=True)
        else:
            img.save(output, format='PNG', optimize=True)
        output.seek(0)

        image_field.save(
            image_field.name,
            InMemoryUploadedFile(
                output,
                'ImageField',
                image_field.name,
                'image/jpeg' if img.mode == 'RGB' else 'image/png',
                sys.getsizeof(output),
                None
            )
        )
    except Exception as e:
        logger.error(f'Сжатие изображения не удалось: {e}')