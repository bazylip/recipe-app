"""
Django command to wait for the database to be available.
"""
import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """Django command to wait for the database."""

    def handle(self, *args, **kwargs):
        self.stdout.write("Waiting for database...")
        is_db_up = False
        while not is_db_up:
            try:
                self.check(databases=["default"])
                is_db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
