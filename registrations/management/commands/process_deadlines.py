from django.core.management.base import BaseCommand

from registrations.deadlines import process_deadlines


class Command(BaseCommand):
    help = (
        "Send 60-day deadline reminders and return overdue registrations to DBGI review "
        "(decisions B6 and B7). Run once a day from Task Scheduler or cron; safe to run again."
    )

    def handle(self, *args, **options):
        summary = process_deadlines()
        self.stdout.write(
            self.style.SUCCESS(
                f"Reminders sent: {summary.reminders}; returned to DBGI review: "
                f"{summary.limits_reached}; hold reminders: {summary.hold_reminders}; "
                f"hold limits reached: {summary.hold_limits_reached}; "
                f"price expiry reminders: {summary.price_reminders}"
            )
        )
