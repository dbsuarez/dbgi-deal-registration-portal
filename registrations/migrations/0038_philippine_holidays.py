from datetime import date

from django.db import migrations

# Nationwide regular holidays and special non-working days from the rest of 2026 through 2027
# (Proclamation No. 1006, s. 2025, and No. 1427, s. 2026). Eid'l Fitr and Eid'l Adha are proclaimed
# separately each year, and local holidays differ by place, so DBGI adds those in Administration.
HOLIDAYS = (
    (date(2026, 11, 30), "Bonifacio Day"),
    (date(2026, 12, 8), "Feast of the Immaculate Conception of Mary"),
    (date(2026, 12, 24), "Christmas Eve"),
    (date(2026, 12, 25), "Christmas Day"),
    (date(2026, 12, 30), "Rizal Day"),
    (date(2026, 12, 31), "Last Day of the Year"),
    (date(2027, 1, 1), "New Year's Day"),
    (date(2027, 2, 6), "Chinese New Year"),
    (date(2027, 3, 25), "Maundy Thursday"),
    (date(2027, 3, 26), "Good Friday"),
    (date(2027, 3, 27), "Black Saturday"),
    (date(2027, 4, 9), "Araw ng Kagitingan"),
    (date(2027, 5, 1), "Labor Day"),
    (date(2027, 6, 12), "Independence Day"),
    (date(2027, 8, 21), "Ninoy Aquino Day"),
    (date(2027, 8, 30), "National Heroes Day"),
    (date(2027, 11, 1), "All Saints' Day"),
    (date(2027, 11, 2), "All Souls' Day"),
    (date(2027, 11, 30), "Bonifacio Day"),
    (date(2027, 12, 8), "Feast of the Immaculate Conception of Mary"),
    (date(2027, 12, 24), "Christmas Eve"),
    (date(2027, 12, 25), "Christmas Day"),
    (date(2027, 12, 30), "Rizal Day"),
    (date(2027, 12, 31), "Last Day of the Year"),
)


def add_holidays(apps, schema_editor):
    """Leaves any date DBGI already entered unchanged."""
    PublicHoliday = apps.get_model("registrations", "PublicHoliday")
    for holiday_date, name in HOLIDAYS:
        PublicHoliday.objects.get_or_create(date=holiday_date, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [
        ("registrations", "0037_merge_split_repeat_orders_holidays"),
    ]

    operations = [
        migrations.RunPython(add_holidays, migrations.RunPython.noop),
    ]
