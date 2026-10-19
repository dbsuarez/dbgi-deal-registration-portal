from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from registrations.models import Company, User


class Command(BaseCommand):
    help = "Create or refresh the local development accounts."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Development accounts can only be seeded when DEBUG is enabled.")

        company, _ = Company.objects.get_or_create(name="DEMO ONLY - Sample Partner")
        company.is_active = True
        company.save(update_fields=["is_active"])

        preview, _ = User.objects.get_or_create(username="preview")
        preview.role = User.Role.COMPANY
        preview.company = company
        preview.is_active = True
        preview.is_staff = False
        preview.is_superuser = False
        preview.set_password("testpass123")
        preview.save()

        admin, _ = User.objects.get_or_create(username="admin-preview")
        admin.role = User.Role.DBGI_ADMIN
        admin.company = None
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("testpass123")
        admin.save()

        self.stdout.write(
            self.style.SUCCESS("Development accounts preview and admin-preview are ready.")
        )
