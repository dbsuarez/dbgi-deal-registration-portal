from django.core.management.base import BaseCommand, CommandError

from registrations.snapshots import SnapshotError, import_backup, restore_snapshot


class Command(BaseCommand):
    help = "Replace all portal data and uploaded files with a backup file from backup_portal."

    def add_arguments(self, parser):
        parser.add_argument("backup", help="The backup file (.zip).")
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm that the current data will be replaced.",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("This replaces all current data. Run it again with --yes.")
        try:
            with open(options["backup"], "rb") as source:
                name = import_backup(source)
            restored = restore_snapshot(name)
        except (OSError, SnapshotError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Restored the backup from {restored['taken_at']}."))
