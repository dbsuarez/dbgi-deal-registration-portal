from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from registrations.models import PortalSetting
from registrations.owner import owner_overview, owners, summary_text


class Command(BaseCommand):
    help = (
        "Email the owner a short Monday summary: prices waiting for him, this month so far, "
        "bids coming up, and what is stuck. Run once a week (deploy/cron.d/dbgi-portal)."
    )

    def handle(self, *args, **options):
        if not PortalSetting.current().owner_weekly_summary:
            self.stdout.write("Owner summary is switched off in Portal settings.")
            return
        text = summary_text(owner_overview())
        text += f"\n\nOpen the portal: {settings.PORTAL_BASE_URL}/"
        sent = 0
        for owner in owners():
            if owner.email.strip():
                send_mail("DBGI portal: your Monday summary", text, None, [owner.email.strip()])
                sent += 1
        self.stdout.write(self.style.SUCCESS(f"Owner summaries sent: {sent}"))
