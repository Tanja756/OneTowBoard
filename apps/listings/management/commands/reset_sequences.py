from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Сбрасывает автоинкременты всех таблиц (SQLite)'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sqlite_sequence")
        self.stdout.write(self.style.SUCCESS('Автоинкременты сброшены'))