from django.db import migrations


INITIAL_PRODUCTS = (
    {
        "code": "M1820W",
        "name": "20 ppm monochrome laser printer",
        "category": "Laser Printers",
    },
    {
        "code": "P1820W",
        "name": "20 ppm monochrome laser printer",
        "category": "Laser Printers",
    },
)


def seed_initial_laser_printers(apps, schema_editor):
    Product = apps.get_model("registrations", "Product")
    database = schema_editor.connection.alias
    for product in INITIAL_PRODUCTS:
        Product.objects.using(database).get_or_create(
            code=product["code"],
            defaults={
                "name": product["name"],
                "category": product["category"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0002_registration_evidence_description_and_more"),
    ]

    operations = [
        migrations.RunPython(
            seed_initial_laser_printers,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
