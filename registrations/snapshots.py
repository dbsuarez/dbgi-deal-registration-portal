"""Snapshots of all portal data for test servers: take one before practice, restore it after.

A snapshot holds every record of the portal's own apps (users, companies, products, prices,
End-users, deals, and settings) and the uploaded files. Restoring replaces the current data with
it. A snapshot stays on the same server, so it is not a backup until it is downloaded: a
downloaded snapshot is a backup file, and uploading one brings it back. The admin screens offer this
only in debug mode; the backup_portal and restore_portal commands work anywhere.
"""

import json
import re
import shutil
import zipfile
from datetime import timedelta
from io import StringIO
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils import timezone

SNAPSHOT_APPS = ("registrations", "devtools")
NAME_PATTERN = re.compile(r"^\d{8}-\d{6}$")
MAX_BACKUP_BYTES = 500 * 1024 * 1024


class SnapshotError(Exception):
    pass


def snapshots_available():
    return settings.DEBUG


def _root():
    return Path(settings.MEDIA_ROOT) / "snapshots"


def _files_root():
    return Path(settings.MEDIA_ROOT) / "private"


def _models():
    return [
        model
        for app in SNAPSHOT_APPS
        for model in apps.get_app_config(app).get_models(include_auto_created=True)
        if model._meta.managed and not model._meta.proxy
    ]


def _folder(name):
    if not NAME_PATTERN.match(name or ""):
        raise SnapshotError("That snapshot does not exist.")
    folder = _root() / name
    if not (folder / "data.json").is_file():
        raise SnapshotError("That snapshot does not exist.")
    return folder


def list_snapshots():
    root = _root()
    if not root.is_dir():
        return []
    found = []
    for folder in sorted(root.iterdir(), reverse=True):
        meta_file = folder / "meta.json"
        if NAME_PATTERN.match(folder.name) and meta_file.is_file():
            found.append({"name": folder.name, **json.loads(meta_file.read_text(encoding="utf-8"))})
    return found


def _new_folder():
    """A new, empty snapshot folder named after the current time."""
    moment = timezone.localtime()
    while (_root() / moment.strftime("%Y%m%d-%H%M%S")).exists():
        moment += timedelta(seconds=1)
    folder = _root() / moment.strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True)
    return folder, moment


def take_snapshot(label=""):
    from .models import Registration, User

    folder, now = _new_folder()
    name = folder.name
    try:
        # Written here as UTF-8: dumpdata's own file output uses the system encoding on Windows.
        buffer = StringIO()
        call_command("dumpdata", *SNAPSHOT_APPS, natural_foreign=True, stdout=buffer, verbosity=0)
        (folder / "data.json").write_text(buffer.getvalue(), encoding="utf-8")
        if _files_root().is_dir():
            shutil.copytree(_files_root(), folder / "files")
        meta = {
            "label": label.strip()[:120],
            "taken_at": now.strftime("%Y-%m-%d %H:%M"),
            "deals": Registration.objects.count(),
            "users": User.objects.count(),
        }
        (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return {"name": name, **meta}


def restore_snapshot(name):
    """Replace all portal data and uploaded files with the snapshot. All or nothing for the data."""
    folder = _folder(name)
    tables = [model._meta.db_table for model in _models()]
    with transaction.atomic():
        statements = connection.ops.sql_flush(no_style(), tables, allow_cascade=True)
        connection.ops.execute_sql_flush(statements)
        call_command("loaddata", str(folder / "data.json"), verbosity=0)
        transaction.on_commit(lambda: _restore_files(folder))
    return json.loads((folder / "meta.json").read_text(encoding="utf-8"))


def _restore_files(folder):
    shutil.rmtree(_files_root(), ignore_errors=True)
    if (folder / "files").is_dir():
        shutil.copytree(folder / "files", _files_root())


def delete_snapshot(name):
    shutil.rmtree(_folder(name))


def export_snapshot(name, target):
    """Write the snapshot as a backup file (a zip) to `target`, a binary file object."""
    folder = _folder(name)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(folder).as_posix())


def _member_allowed(member):
    path = PurePosixPath(member)
    return (
        not path.is_absolute()
        and "\\" not in member
        and ".." not in path.parts
        and (member in {"data.json", "meta.json"} or path.parts[0] == "files")
    )


def import_backup(source):
    """Add a downloaded backup file as a snapshot, ready to restore. Returns its name."""
    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile as error:
        raise SnapshotError("That file is not a portal backup.") from error
    with archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        names = {info.filename for info in members}
        if not {"data.json", "meta.json"} <= names or not all(map(_member_allowed, names)):
            raise SnapshotError("That file is not a portal backup.")
        if sum(info.file_size for info in members) > MAX_BACKUP_BYTES:
            raise SnapshotError("That backup is too large.")
        try:
            meta = json.loads(archive.read("meta.json"))
            if (
                not isinstance(json.loads(archive.read("data.json")), list)
                or "taken_at" not in meta
            ):
                raise ValueError
        except ValueError as error:
            raise SnapshotError("That file is not a portal backup.") from error
        folder, _ = _new_folder()
        try:
            for info in members:
                target = folder / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as read, open(target, "wb") as written:
                    shutil.copyfileobj(read, written)
            meta["label"] = f"{meta.get('label') or 'Backup'} (uploaded)"[:140]
            (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
    return folder.name
