from .models import RegistrationNotification, User


def notify_company_users(
    *,
    registration,
    event_type,
    event_key,
    title,
    message,
):
    """Create one durable, tenant-scoped notification per active company user."""
    recipient_ids = User.objects.filter(
        company_id=registration.company_id,
        role=User.Role.COMPANY,
        is_active=True,
    ).values_list("id", flat=True)
    RegistrationNotification.objects.bulk_create(
        [
            RegistrationNotification(
                recipient_id=recipient_id,
                registration=registration,
                event_type=event_type,
                event_key=event_key,
                title=title,
                message=message,
            )
            for recipient_id in recipient_ids
        ],
        ignore_conflicts=True,
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
