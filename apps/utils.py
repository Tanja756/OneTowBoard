import uuid
import os

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