from django.db import migrations


def backfill_commercial_review(apps, schema_editor):
    Registration = apps.get_model("registrations", "Registration")
    RegistrationCategoryApproval = apps.get_model("registrations", "RegistrationCategoryApproval")
    RegistrationItem = apps.get_model("registrations", "RegistrationItem")

    for item in RegistrationItem.objects.select_related("product").iterator():
        if item.product_id:
            item.currency = item.product.currency
            item.list_unit_price_snapshot = item.product.list_price
            item.save(update_fields=["currency", "list_unit_price_snapshot"])

    for registration in Registration.objects.iterator():
        categories = (
            RegistrationItem.objects.filter(
                registration_id=registration.pk, product_id__isnull=False
            )
            .values_list("product__category", flat=True)
            .distinct()
        )
        RegistrationCategoryApproval.objects.bulk_create(
            [
                RegistrationCategoryApproval(
                    registration_id=registration.pk,
                    category=category,
                    status="pending",
                )
                for category in categories
            ],
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):
    dependencies = [("registrations", "0011_opportunity_project_status_product_currency_and_more")]

    operations = [migrations.RunPython(backfill_commercial_review, migrations.RunPython.noop)]
