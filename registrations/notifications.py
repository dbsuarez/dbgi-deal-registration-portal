import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
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
            subject=f"DBGI Project Registration: {notification.title}",
            body=(
                f"{notification.message}\n\n"
                f"Open the portal: {settings.PORTAL_BASE_URL}/notifications/\n\n"
                "This email contains a summary only. The portal notification is the "
                "authoritative record."
            ),
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


def notify_company_users(
    *,
    registration,
    event_type,
    event_key,
    title,
    message,
):
    """Create one durable, tenant-scoped notification per active company user."""
    recipients = User.objects.filter(
        company_id=registration.company_id,
        role=User.Role.COMPANY,
        is_active=True,
    ).only("id", "email")
    email_enabled = NotificationEventSetting.objects.filter(
        event_type=event_type,
        email_enabled=True,
    ).exists()
    for recipient in recipients:
        email_address = recipient.email.strip()
        email_status = (
            RegistrationNotification.EmailStatus.PENDING
            if email_enabled and email_address
            else RegistrationNotification.EmailStatus.SKIPPED
            if email_enabled
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
            },
        )
        if created and email_status == RegistrationNotification.EmailStatus.PENDING:
            transaction.on_commit(
                lambda notification_id=notification.pk: deliver_notification_email(notification_id)
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
        "request_changes": "Changes requested",
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
        registration.Status.CHANGES_REQUESTED: "Changes requested",
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
