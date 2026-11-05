from django.db import migrations, models


def move_approved_deals(apps, schema_editor):
    """A linked deal returns to Registered, so it is ranked again. An unlinked one goes back to DBGI."""
    Registration = apps.get_model("registrations", "Registration")
    RegistrationEvent = apps.get_model("registrations", "RegistrationEvent")
    for registration in Registration.objects.filter(status="approved"):
        registration.status = (
            "eligible_matched" if registration.opportunity_scope_id else "under_review"
        )
        registration.save(update_fields=["status"])
        RegistrationEvent.objects.create(
            registration=registration,
            actor=None,
            event_type="Status updated",
            details='The registration status "Approved" was removed from the portal.',
            snapshot={},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("registrations", "0038_philippine_holidays"),
    ]

    operations = [
        migrations.RunPython(move_approved_deals, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="registration",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("under_review", "Under review"),
                    ("changes_requested", "Returned for changes"),
                    ("resubmitted", "Resubmitted"),
                    ("eligible_matched", "Registered"),
                    ("review_required", "Review required after edit"),
                    ("rejected", "Rejected"),
                    ("withdrawn", "Withdrawn"),
                ],
                default="submitted",
                max_length=20,
            ),
        ),
    ]
