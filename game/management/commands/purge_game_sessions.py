from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from game.models import GameSession
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Purge GameSession records older than a specified number of days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Specify the number of days to retain GameSession records.',
        )

    def handle(self, *args, **options):
        days = options['days']
        threshold_date = timezone.now() - timedelta(days=days)
        logger.info(f"Starting purge of GameSession records older than {days} day(s).")

        try:
            old_sessions = GameSession.objects.filter(last_active__lt=threshold_date)
            count = old_sessions.count()
            if count == 0:
                logger.info("No GameSession records found to delete.")
                self.stdout.write(self.style.WARNING(
                    f'No GameSession records older than {days} days were found.'
                ))
                return

            deleted, _ = old_sessions.delete()
            logger.info(f"Successfully deleted {deleted} GameSession record(s) older than {days} day(s).")
            self.stdout.write(self.style.SUCCESS(
                f'Successfully deleted {deleted} GameSession record(s) older than {days} day(s).'
            ))

        except Exception as e:
            logger.exception(f"An error occurred while purging GameSession records: {e}")
            self.stderr.write(self.style.ERROR(
                f'An error occurred while purging GameSession records: {e}'
            ))