import uuid
import os
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

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
    Сжимает изображение в image_field (FileField/ImageField) при превышении max_dim по большей стороне.
    Заменяет содержимое файла оптимизированным вариантом.
    """
    # Открываем изображение с помощью Pillow
    img = Image.open(image_field.file)
    # Если формат не поддерживает прозрачность при сохранении в JPEG, конвертируем
    if img.mode in ('RGBA', 'LA', 'P') and img.format != 'GIF':
        # Конвертируем в RGB для JPEG
        if img.format != 'PNG':  # PNG оставим как есть, он поддерживает прозрачность
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

    # Сохраняем в BytesIO
    output = BytesIO()
    # Определяем формат сохранения (JPEG для RGB, PNG для остальных)
    if img.mode == 'RGB':
        img.save(output, format='JPEG', quality=85, optimize=True)
    else:
        img.save(output, format='PNG', optimize=True)
    output.seek(0)

    # Заменяем файл в поле
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