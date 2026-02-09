from django.core.management.base import BaseCommand

from weather.sqlalchemy_db import init_db


class Command(BaseCommand):
    help = "Initialize SQLAlchemy tables for weather data"

    def handle(self, *args, **options):
        init_db()
        self.stdout.write(self.style.SUCCESS("SQLAlchemy tables initialized."))
