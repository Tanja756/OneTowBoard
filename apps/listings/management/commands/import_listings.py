import os
import json
import glob
import re
from random import randint
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.auth import get_user_model
from django.utils import timezone
from listings.models import Listing, ListingImage
from categories.models import Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Импорт объявлений со сроком 7 дней и случайной датой/временем (вчера)'

    def add_arguments(self, parser):
        parser.add_argument('source_dir', type=str, help='Путь к корневой папке с объявлениями')
        parser.add_argument('--category', type=str, help='Slug категории по умолчанию', default=None)
        parser.add_argument('--param', nargs=2, action='append', metavar=('KEY', 'VALUE'),
                            help='Параметр категории (можно указать несколько)')

    def clean_title(self, raw_title):
        """Удаляет из начала заголовка номер вида '№868137 - ' или '868137 - '"""
        return re.sub(r'^№?\s*\d+\s*[-–—]\s*', '', raw_title).strip()

    def extract_price(self, raw_price):
        """Извлекает первое целое число из строки, иначе None."""
        if not raw_price:
            return None
        match = re.search(r'\d+', raw_price)
        return int(match.group()) if match else None

    def handle(self, *args, **options):
        source = options['source_dir']
        default_category_slug = options.get('category')
        default_params = {}
        if options.get('param'):
            for key, value in options['param']:
                default_params[key] = value

        # Автор по умолчанию – первый суперпользователь
        default_author = User.objects.filter(is_superuser=True).first()
        if not default_author:
            self.stderr.write(self.style.ERROR('Не найден суперпользователь для автора'))
            return

        # Базовая дата – вчера, полночь
        yesterday = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

        created_count = 0
        updated_count = 0
        errors = 0

        for folder in sorted(os.listdir(source)):
            full_path = os.path.join(source, folder)
            if not os.path.isdir(full_path):
                continue

            external_id = folder

            # Заголовок
            title_file = os.path.join(full_path, 'title.txt')
            if not os.path.isfile(title_file):
                self.stdout.write(self.style.WARNING(f'{external_id}: отсутствует title.txt'))
                errors += 1
                continue
            try:
                raw_title = open(title_file, 'r', encoding='utf-8').read().strip()
                if not raw_title:
                    raise ValueError('Пустой заголовок')
                title = self.clean_title(raw_title)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'{external_id}: ошибка чтения title.txt – {e}'))
                errors += 1
                continue

            # Описание
            description = ''
            desc_file = os.path.join(full_path, 'description.txt')
            if os.path.isfile(desc_file):
                try:
                    description = open(desc_file, 'r', encoding='utf-8').read().strip()
                except:
                    pass

            # Цена
            price = None
            price_file = os.path.join(full_path, 'price.txt')
            if os.path.isfile(price_file):
                try:
                    raw_price = open(price_file, 'r').read().strip()
                    price = self.extract_price(raw_price)
                except:
                    pass

            # Телефон объявления
            phone = ''
            phone_file = os.path.join(full_path, 'phone.txt')
            if os.path.isfile(phone_file):
                try:
                    phone = open(phone_file, 'r').read().strip()
                except:
                    pass

            # Категория
            category = None
            category_file = os.path.join(full_path, 'category.txt')
            if os.path.isfile(category_file):
                try:
                    cat_slug = open(category_file, 'r').read().strip()
                    category = Category.objects.get(slug=cat_slug)
                except Category.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'{external_id}: категория "{cat_slug}" не найдена'))
            elif default_category_slug:
                try:
                    category = Category.objects.get(slug=default_category_slug)
                except Category.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Категория по умолчанию не найдена'))

            # Параметры категории
            parameters = {}
            params_file = os.path.join(full_path, 'params.json')
            if os.path.isfile(params_file):
                try:
                    with open(params_file, 'r', encoding='utf-8') as f:
                        parameters = json.load(f)
                except:
                    self.stdout.write(self.style.WARNING(f'{external_id}: не удалось прочитать params.json'))
            else:
                parameters = default_params.copy()

            # Генерируем случайное время вчерашнего дня (от 00:00 до 23:59:59)
            random_seconds = randint(0, 86399)
            created = yesterday + timedelta(seconds=random_seconds)
            expiry = created + timedelta(days=7)

            # Создание или обновление
            listing, is_new = Listing.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'title': title,
                    'description': description,
                    'price': price,
                    'contact_phone': phone,
                    'category': category,
                    'parameters': parameters,
                    'author': default_author,
                    'status': 'active',
                    'created_at': created,
                    'expiry_date': expiry.date(),
                }
            )
            # Принудительно обновляем дату создания, если объявление уже существовало
            if not is_new:
                listing.created_at = created
                listing.expiry_date = expiry.date()
                listing.save(update_fields=['created_at', 'expiry_date'])

            # Загрузка изображений (исключаем файлы phone.*)
            listing.images.all().delete()
            images = []
            for ext in ('*.jpg', '*.jpeg', '*.png', '*.gif'):
                images.extend(glob.glob(os.path.join(full_path, ext)))
            images.sort()
            for img_path in images:
                if os.path.basename(img_path).lower().startswith('phone'):
                    continue
                with open(img_path, 'rb') as f:
                    django_file = File(f, name=os.path.basename(img_path))
                    ListingImage.objects.create(listing=listing, image=django_file)

            if is_new:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(self.style.SUCCESS(f'{"Создано" if is_new else "Обновлено"}: {external_id}'))

        self.stdout.write(self.style.SUCCESS(
            f'Импорт завершён. Создано: {created_count}, обновлено: {updated_count}, ошибок: {errors}'
        ))