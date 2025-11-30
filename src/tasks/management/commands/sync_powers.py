"""
Management command to sync shop powers from code to database.
Run this after adding new powers to power_handlers.py
"""
from django.core.management.base import BaseCommand
from tasks.power_handlers import sync_powers_to_db


class Command(BaseCommand):
    help = 'Sync shop power definitions from code to database'

    def handle(self, *args, **options):
        self.stdout.write('Syncing powers from code to database...')
        sync_powers_to_db()
        self.stdout.write(self.style.SUCCESS('✓ Powers synced successfully!'))
