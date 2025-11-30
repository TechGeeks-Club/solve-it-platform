"""
Django management command to consume judge results from Kafka
Run with: python manage.py consume_results
"""
import asyncio
from django.core.management.base import BaseCommand
from tasks.kafka_consumer import result_consumer_loop


class Command(BaseCommand):
    help = 'Consumes judge results from Kafka and updates submissions in database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Kafka result consumer...'))
        
        try:
            asyncio.run(result_consumer_loop())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nConsumer stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
