from django.db import migrations


ORGANIZATION_TYPES = (
    "Attached agency",
    "Barangay",
    "Bureau",
    "City government",
    "Department",
    "Government hospital",
    "Government-owned or controlled corporation",
    "Municipality",
    "Other government entity",
    "Province",
    "Procuring entity",
    "Public school",
    "State university or college",
)

SECTORS = (
    "Agriculture",
    "Education",
    "Energy",
    "Environment",
    "Finance",
    "General government",
    "Government",
    "Health",
    "Information and communications technology",
    "Infrastructure",
    "Justice",
    "Labor",
    "National defense",
    "Other",
    "Public safety",
    "Social protection",
    "Transportation",
    "Utilities",
)


def normalize(value):
    import re

    return " ".join(re.sub(r"[^a-z0-9 ]", " ", value.lower()).split())


def seed_classifications(apps, schema_editor):
    EndUser = apps.get_model("registrations", "EndUser")
    Classification = apps.get_model("registrations", "EndUserClassificationOption")
    EndUser.objects.filter(government_branch="Executive").update(
        government_branch="National government"
    )
    rows = [
        Classification(
            category=category,
            name=name,
            normalized_name=normalize(name),
            status="approved",
        )
        for category, values in (
            ("organization_type", ORGANIZATION_TYPES),
            ("sector", SECTORS),
        )
        for name in values
    ]
    Classification.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [("registrations", "0024_alter_enduser_government_branch_and_more")]

    operations = [migrations.RunPython(seed_classifications, migrations.RunPython.noop)]
