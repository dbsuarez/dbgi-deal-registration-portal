from pathlib import Path

from django.core.management.base import BaseCommand

from registrations.snapshots import delete_snapshot, export_snapshot, take_snapshot


class Command(BaseCommand):
    help = (
        "Save all portal data and uploaded files as one backup file. Copy the file off the server: "
        "a backup kept only on the same server is lost with it."
    )

    def add_arguments(self, parser):
        parser.add_argument("--output", default=".", help="Folder for the backup file.")
        parser.add_argument("--label", default="Backup", help="A short note saved with it.")

    def handle(self, *args, **options):
        snapshot = take_snapshot(options["label"])
        output = Path(options["output"])
        output.mkdir(parents=True, exist_ok=True)
        path = output / f"dbgi-portal-backup-{snapshot['name']}.zip"
        try:
            with open(path, "wb") as target:
                export_snapshot(snapshot["name"], target)
        finally:
            delete_snapshot(snapshot["name"])
        self.stdout.write(self.style.SUCCESS(f"Backup saved: {path}"))
