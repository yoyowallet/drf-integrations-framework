from django.core.management.base import BaseCommand

from drf_integrations.models import Application


class Command(BaseCommand):
    help = "Synchronizes the integrations registry with the DB"

    def handle(self, *args, **options):
        self.stdout.write("==> Syncing integrations")
        Application.objects.sync_with_integration_registry()
        self.stdout.write(self.style.SUCCESS("Registry successfully synchronized"))
