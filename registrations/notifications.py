import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import NotificationEventSetting, RegistrationNotification, User

logger = logging.getLogger(__name__)


def deliver_notification_email(notification_id):
    notification = RegistrationNotification.objects.select_related("registration").get(
        pk=notification_id
    )
    if notification.email_status != RegistrationNotification.EmailStatus.PENDING:
        return
    notification.email_attempts += 1
    notification.email_last_attempt_at = timezone.now()
    try:
        EmailMessage(
            subject=notification.email_subject,
            body=notification.email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.email_address],
        ).send(fail_silently=False)
    except Exception as exc:
        notification.email_status = RegistrationNotification.EmailStatus.FAILED
        notification.email_error = str(exc)[:500]
        logger.exception(
            "Notification email delivery failed", extra={"notification_id": notification_id}
        )
    else:
        notification.email_status = RegistrationNotification.EmailStatus.SENT
        notification.email_sent_at = timezone.now()
        notification.email_error = ""
    notification.save(
        update_fields=[
            "email_status",
            "email_attempts",
            "email_last_attempt_at",
            "email_sent_at",
            "email_error",
        ]
    )


def retry_notification_email(notification):
    if not notification.email_address or notification.email_status not in {
        RegistrationNotification.EmailStatus.FAILED,
        RegistrationNotification.EmailStatus.PENDING,
    }:
        return False
    notification.email_status = RegistrationNotification.EmailStatus.PENDING
    notification.email_error = ""
    notification.save(update_fields=["email_status", "email_error"])
    deliver_notification_email(notification.pk)
    return True


def _notify(recipients, *, registration, event_type, event_key, title, message, emailed):
    """Create one portal notification per recipient; email those for whom `emailed` is True.

    Email also needs the event type switched on in the notification settings (off without one).
    """
    event_setting = NotificationEventSetting.objects.filter(event_type=event_type).first()
    email_enabled = bool(event_setting and event_setting.email_enabled)
    email_subject = email_body = ""
    if email_enabled:
        email_subject, email_body = event_setting.render_email(
            {
                "title": title,
                "message": message,
                "registration_reference": registration.reference,
                "portal_url": settings.PORTAL_BASE_URL,
            }
        )
    for recipient in recipients:
        send = email_enabled and emailed(recipient)
        email_address = recipient.email.strip() if send else ""
        email_status = (
            RegistrationNotification.EmailStatus.PENDING
            if send and email_address
            else RegistrationNotification.EmailStatus.SKIPPED
            if send
            else RegistrationNotification.EmailStatus.NOT_REQUESTED
        )
        notification, created = RegistrationNotification.objects.get_or_create(
            recipient=recipient,
            event_key=event_key,
            defaults={
                "registration": registration,
                "event_type": event_type,
                "title": title,
                "message": message,
                "email_address": email_address,
                "email_status": email_status,
                "email_subject": email_subject if send else "",
                "email_body": email_body if send else "",
            },
        )
        if created and email_status == RegistrationNotification.EmailStatus.PENDING:
            transaction.on_commit(
                lambda notification_id=notification.pk: deliver_notification_email(notification_id)
            )


def notify_company_users(*, registration, event_type, event_key, title, message):
    """Notify every active company user in the portal; email only the submitter (decision D2)."""
    recipients = User.objects.filter(
        company_id=registration.company_id,
        role=User.Role.COMPANY,
        is_active=True,
    ).only("id", "email")
    _notify(
        recipients,
        registration=registration,
        event_type=event_type,
        event_key=event_key,
        title=title,
        message=message,
        emailed=lambda user: user.pk == registration.submitted_by_id,
    )


def notify_dbgi_admins(*, registration, event_type, event_key, title, message, email=False):
    """Notify every active DBGI administrator in the portal; also email them when `email` is set,
    which is used when the event needs DBGI's action (decision D2)."""
    # Same rule as User.is_dbgi_admin
    administrators = User.objects.filter(
        Q(is_superuser=True) | Q(is_staff=True, role=User.Role.DBGI_ADMIN), is_active=True
    ).only("id", "email")
    _notify(
        administrators,
        registration=registration,
        event_type=event_type,
        event_key=event_key,
        title=title,
        message=message,
        emailed=lambda user: email,
    )


def notify_dbgi_review_needed(registration, reason):
    """A registration waits for DBGI review: new, resubmitted, or edited after confirmation."""
    notify_dbgi_admins(
        registration=registration,
        event_type=RegistrationNotification.EventType.REVIEW_NEEDED,
        event_key=f"registration:{registration.pk}:review-needed:v{registration.version}",
        title=f"Review needed: {reason}",
        message=(
            f"{registration.reference} ({registration.project_title}) from "
            f"{registration.company.name}: {reason}. Open the registration to review it."
        ),
        email=True,
    )


def notify_dbgi_renewal_requested(approval, renewal):
    registration = approval.registration
    notify_dbgi_admins(
        registration=registration,
        event_type=RegistrationNotification.EventType.RENEWAL_REQUESTED,
        event_key=f"renewal:{renewal.pk}:requested",
        title="Price renewal requested",
        message=(
            f"{registration.company.name} asked to renew the approved {approval.category} prices "
            f"for {registration.reference}. Open the registration to decide."
        ),
        email=True,
    )


def notify_dbgi_withdrawal(registration, reason):
    notify_dbgi_admins(
        registration=registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_WITHDRAWN,
        event_key=f"registration:{registration.pk}:withdrawn",
        title="Registration withdrawn",
        message=(
            f"{registration.company.name} withdrew {registration.reference} "
            f"({registration.project_title}). Reason: {reason}"
        ),
    )


def notify_outcome_reported(report):
    registration = report.registration
    notify_dbgi_admins(
        registration=registration,
        event_type=RegistrationNotification.EventType.OUTCOME_REPORTED,
        event_key=f"outcome-report:{report.pk}:reported",
        email=True,
        title=f"Project reported {report.get_outcome_display().lower()}",
        message=(
            f"{registration.company.name} reported {registration.reference} "
            f"({registration.project_title}) as {report.get_outcome_display()}. "
            f"Note: {report.note} Open the registration to confirm or decline."
        ),
    )


def notify_outcome_decision(report):
    registration = report.registration
    accepted = report.status == report.Status.CONFIRMED
    notify_company_users(
        registration=registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        event_key=f"outcome-report:{report.pk}:{report.status}",
        title="Project outcome confirmed" if accepted else "Project outcome not accepted",
        message=(
            f"DBGI {'confirmed' if accepted else 'did not accept'} your "
            f"{report.get_outcome_display()} report for {registration.reference}. "
            "Open the registration to read DBGI's note."
        ),
    )


def notify_submission(registration):
    notify_company_users(
        registration=registration,
        event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
        event_key=f"registration:{registration.pk}:submitted",
        title="Submission confirmed",
        message=(
            f"{registration.reference} was submitted successfully. "
            "DBGI will notify you when a registration decision is available."
        ),
    )


def notify_registration_decision(registration, decision):
    labels = {
        "request_changes": "Returned for changes",
        "confirm_match": "Registration confirmed",
        "reject": "Registration rejected",
    }
    title = labels.get(decision.decision)
    if not title:
        return
    notify_company_users(
        registration=registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        event_key=f"review-decision:{decision.pk}",
        title=title,
        message=(
            f"DBGI completed a registration review action for {registration.reference}. "
            "Open the registration to review the decision and reason."
        ),
    )


def notify_admin_status_change(registration, previous_status):
    labels = {
        registration.Status.CHANGES_REQUESTED: "Returned for changes",
        registration.Status.ELIGIBLE_MATCHED: "Registration confirmed",
        registration.Status.APPROVED: "Registration approved",
        registration.Status.REJECTED: "Registration rejected",
    }
    title = labels.get(registration.status)
    if not title or registration.status == previous_status:
        return
    notify_company_users(
        registration=registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        event_key=f"admin-status:{registration.pk}:v{registration.version}",
        title=title,
        message=(
            f"DBGI updated the registration decision for {registration.reference}. "
            "Open the registration to review its current status."
        ),
    )


def notify_automatic_match(registration, suggestion):
    notify_company_users(
        registration=registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        event_key=f"automatic-match:{suggestion.pk}",
        title="Registration confirmed",
        message=(
            f"{registration.reference} was matched to an eligible opportunity scope. "
            "Open the registration to review its current status."
        ),
    )


def notify_price_decision(approval):
    notify_company_users(
        registration=approval.registration,
        event_type=RegistrationNotification.EventType.PRICE_DECISION,
        event_key=f"price-decision:{approval.pk}:v{approval.version}",
        title=f"Price request {approval.get_status_display().lower()}",
        message=(
            f"DBGI updated the {approval.category} price request for "
            f"{approval.registration.reference}. Open the registration to review the terms."
        ),
    )
