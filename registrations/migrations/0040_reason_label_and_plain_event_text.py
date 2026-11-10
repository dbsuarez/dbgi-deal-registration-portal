import re

from django.db import migrations, models

PRICE = re.compile(r"^(.+) pricing was marked (.+) through Django administration\.$")
PROJECT = re.compile(r"^Project status changed from (.+) to (.+) through Django administration\.$")


def plain_event_text(apps, schema_editor):
    """Activity notes partners can read no longer name the software DBGI used."""
    RegistrationEvent = apps.get_model("registrations", "RegistrationEvent")
    for event in RegistrationEvent.objects.filter(details__endswith="through Django administration."):
        price = PRICE.match(event.details)
        project = PROJECT.match(event.details)
        if price:
            event.details = f"DBGI marked the {price[1]} price {price[2]}."
        elif project:
            event.details = f"DBGI changed the project status from {project[1]} to {project[2]}."
        else:
            continue
        event.save(update_fields=["details"])


class Migration(migrations.Migration):
    dependencies = [
        ("registrations", "0039_remove_approved_registration_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registrationcategoryapproval",
            name="rationale",
            field=models.TextField(blank=True, verbose_name="reason"),
        ),
        migrations.AlterField(
            model_name="registrationreviewdecision",
            name="rationale",
            field=models.TextField(verbose_name="reason"),
        ),
        migrations.RunPython(plain_event_text, migrations.RunPython.noop),
    ]
