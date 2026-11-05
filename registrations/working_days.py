"""Working days: Monday to Friday, no Philippine public holidays, 5:00 PM cutoff (decision D4)."""

from datetime import timedelta

from django.utils import timezone

from .models import PublicHoliday

CUTOFF_HOUR = 17


def add_working_days(start, days):
    """The date `days` working days after `start`. After the cutoff, or on a day off, counting
    starts from the next working day."""
    current = timezone.localtime(start)
    current_date = current.date()
    last_possible = current_date + timedelta(days=days * 7 + 60)
    holidays = set(
        PublicHoliday.objects.filter(date__range=(current_date, last_possible)).values_list(
            "date", flat=True
        )
    )

    def is_working(day):
        return day.weekday() < 5 and day not in holidays

    if current.hour >= CUTOFF_HOUR or not is_working(current_date):
        current_date += timedelta(days=1)
        while not is_working(current_date):
            current_date += timedelta(days=1)
    for _ in range(days):
        current_date += timedelta(days=1)
        while not is_working(current_date):
            current_date += timedelta(days=1)
    return current_date
