from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from audit.models import SystemLog

class Command(BaseCommand):
    help = 'Purge or archive audit logs older than N days (default 90).'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90, help='Age in days beyond which logs are purged')
        parser.add_argument('--dry-run', action='store_true', help='Only report how many would be deleted')

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)
        qs = SystemLog.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        if options['dry_run']:
            self.stdout.write(self.style.NOTICE(f"[DRY RUN] {count} logs older than {days} days would be deleted."))
            return
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} logs older than {days} days."))