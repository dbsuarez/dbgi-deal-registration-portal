"""60-day deadlines (decisions B6 and B7), processed once a day by `manage.py process_deadlines`.

B6: a registration DBGI has not confirmed gets a reminder 7 days before its 60-day limit, then goes
back to DBGI for review on day 60. It is never rejected automatically.
B7: while a project is on hold, its linked registrations keep their place for 60 days, with the same
reminder, then DBGI reviews them.
Days are calendar days. Each step is recorded on the row, so running the job twice changes nothing.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .audit import registration_snapshot
from .models import Opportunity, Registration, RegistrationEvent, RegistrationNotification
from .notifications import notify_company_users, notify_dbgi_admins

LIMIT_DAYS = 60
REMINDER_DAYS_BEFORE = 7

UNCONFIRMED_STATUSES = {
    Registration.Status.SUBMITTED,
    Registration.Status.UNDER_REVIEW,
    Registration.Status.CHANGES_REQUESTED,
    Registration.Status.RESUBMITTED,
}
LINKED_STATUSES = {Registration.Status.ELIGIBLE_MATCHED, Registration.Status.APPROVED}


@dataclass
class DeadlineSummary:
    reminders: int = 0
    limits_reached: int = 0
    hold_reminders: int = 0
    hold_limits_reached: int = 0


def _flag_for_review(registration, now, title, details):
    registration.needs_review = True
    registration.save(update_fields=["needs_review", "updated_at"])
    RegistrationEvent.objects.create(
        registration=registration,
        event_type=title,
        details=details,
        snapshot=registration_snapshot(registration),
    )


def process_deadlines(now=None):
    now = now or timezone.now()
    reminder_cutoff = now - timedelta(days=LIMIT_DAYS - REMINDER_DAYS_BEFORE)
    limit_cutoff = now - timedelta(days=LIMIT_DAYS)
    summary = DeadlineSummary()

    # B6: registrations still waiting for DBGI's confirmation
    waiting = Registration.objects.filter(
        status__in=UNCONFIRMED_STATUSES, limit_reached_at__isnull=True
    )
    for pk in waiting.filter(original_submitted_at__lte=limit_cutoff).values_list("pk", flat=True):
        with transaction.atomic():
            registration = (
                Registration.objects.select_for_update().select_related("company").get(pk=pk)
            )
            if registration.limit_reached_at or registration.status not in UNCONFIRMED_STATUSES:
                continue
            registration.limit_reached_at = now
            registration.save(update_fields=["limit_reached_at"])
            _flag_for_review(
                registration,
                now,
                "60-day limit reached",
                "Not confirmed within 60 days of submission. DBGI must review it.",
            )
            notify_dbgi_admins(
                registration=registration,
                event_type=RegistrationNotification.EventType.DEADLINE_REACHED,
                event_key=f"registration:{registration.pk}:limit-reached",
                title="60-day limit reached",
                message=(
                    f"{registration.reference} ({registration.project_title}) from "
                    f"{registration.company.name} was not confirmed within 60 days. Review it."
                ),
            )
            summary.limits_reached += 1
    reminders = waiting.filter(
        original_submitted_at__lte=reminder_cutoff, limit_reminder_sent_at__isnull=True
    )
    for pk in reminders.values_list("pk", flat=True):
        with transaction.atomic():
            registration = Registration.objects.select_for_update().get(pk=pk)
            if registration.limit_reminder_sent_at or registration.limit_reached_at:
                continue
            registration.limit_reminder_sent_at = now
            registration.save(update_fields=["limit_reminder_sent_at"])
            notify_company_users(
                registration=registration,
                event_type=RegistrationNotification.EventType.DEADLINE_REMINDER,
                event_key=f"registration:{registration.pk}:limit-reminder",
                title="7 days left for DBGI confirmation",
                message=(
                    f"{registration.reference} reaches its 60-day limit in 7 days without DBGI "
                    "confirmation. DBGI will then review it. Make sure its details and evidence "
                    "are complete."
                ),
            )
            summary.reminders += 1

    # B7: projects on hold
    on_hold = Opportunity.objects.filter(
        project_status=Opportunity.ProjectStatus.ON_HOLD,
        on_hold_since__isnull=False,
        hold_limit_reached_at__isnull=True,
    )
    for pk in on_hold.filter(on_hold_since__lte=limit_cutoff).values_list("pk", flat=True):
        with transaction.atomic():
            opportunity = Opportunity.objects.select_for_update().get(pk=pk)
            if opportunity.hold_limit_reached_at:
                continue
            opportunity.hold_limit_reached_at = now
            opportunity.save(update_fields=["hold_limit_reached_at"])
            for registration in _linked(opportunity):
                _flag_for_review(
                    registration,
                    now,
                    "60-day hold limit reached",
                    "The project has been on hold for 60 days. DBGI must review it.",
                )
                notify_dbgi_admins(
                    registration=registration,
                    event_type=RegistrationNotification.EventType.DEADLINE_REACHED,
                    event_key=f"opportunity:{opportunity.pk}:hold-limit:{registration.pk}",
                    title="60-day hold limit reached",
                    message=(
                        f"{registration.reference} ({registration.project_title}): the project "
                        "has been on hold for 60 days. Review it."
                    ),
                )
            summary.hold_limits_reached += 1
    hold_reminders = on_hold.filter(
        on_hold_since__lte=reminder_cutoff, hold_reminder_sent_at__isnull=True
    )
    for pk in hold_reminders.values_list("pk", flat=True):
        with transaction.atomic():
            opportunity = Opportunity.objects.select_for_update().get(pk=pk)
            if opportunity.hold_reminder_sent_at or opportunity.hold_limit_reached_at:
                continue
            opportunity.hold_reminder_sent_at = now
            opportunity.save(update_fields=["hold_reminder_sent_at"])
            for registration in _linked(opportunity):
                notify_company_users(
                    registration=registration,
                    event_type=RegistrationNotification.EventType.DEADLINE_REMINDER,
                    event_key=(
                        f"opportunity:{opportunity.pk}:hold-reminder:"
                        f"{opportunity.on_hold_since:%Y%m%d}:{registration.pk}"
                    ),
                    title="7 days left on the project hold",
                    message=(
                        f"The project for {registration.reference} has been on hold for 53 days. "
                        "Your place is kept for 60 days; DBGI will then review it."
                    ),
                )
            summary.hold_reminders += 1
    return summary


def _linked(opportunity):
    return list(
        Registration.objects.select_for_update()
        .select_related("company")
        .filter(opportunity_scope__opportunity=opportunity, status__in=LINKED_STATUSES)
    )
