"""Merging projects and splitting deals: DBGI decides each case with a written reason (decision B3).

Original submission times are never rewritten. Companies read a plain notice; the reason is for DBGI
only, because it may name another company.
"""

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from .audit import registration_snapshot
from .models import (
    OpportunityScope,
    PriceApprovalRenewal,
    ProjectChange,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationNotification,
    RepeatOrder,
)
from .notifications import notify_company_users
from .ranking import latest_rank_orders, latest_tie_decisions, rank_scope, ranked_registrations

REASON_MARK = " DBGI reason: "
MERGED_EVENT = "Project merged"
SPLIT_EVENT = "Deal split"
PROJECT_CHANGE_EVENTS = frozenset({MERGED_EVENT, SPLIT_EVENT})

CLOSED_STATUSES = frozenset({Registration.Status.WITHDRAWN, Registration.Status.REJECTED})
SPLITTABLE_STATUSES = frozenset(
    {
        Registration.Status.ELIGIBLE_MATCHED,
        Registration.Status.REVIEW_REQUIRED,
    }
)


class ProjectChangeError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def public_details(details):
    """What a company may read of a project change event."""
    return details.split(REASON_MARK)[0]


def _active_scopes(*scope_ids):
    scopes = {
        scope.pk: scope
        for scope in OpportunityScope.objects.select_related("opportunity").filter(
            pk__in=scope_ids, is_active=True, opportunity__is_active=True
        )
    }
    if len(scopes) != len(set(scope_ids)):
        raise ProjectChangeError(
            "scope_unavailable", "That project is not active. Refresh and try again."
        )
    return scopes


def merge_preview(source_id, target_id):
    """The combined order by original submission time, each company once, changing nothing."""
    if source_id == target_id:
        raise ProjectChangeError("same_scope", "Choose a different project to merge into.")
    scopes = _active_scopes(source_id, target_id)
    scope_ids = [source_id, target_id]
    ranked = ranked_registrations(scope_ids)
    decisions = latest_tie_decisions(scope_ids)
    orders = latest_rank_orders(scope_ids)
    current = {}
    for scope_id in scope_ids:
        for entry in rank_scope(scope_id, ranked[scope_id], decisions, orders.get(scope_id)):
            current[entry.registration.pk] = entry.rank
    combined = sorted(
        [*ranked[source_id], *ranked[target_id]],
        key=lambda item: (item.original_submitted_at, item.pk),
    )
    seen_companies = set()
    rows = []
    for registration in combined:
        if registration.company_id in seen_companies:
            continue
        seen_companies.add(registration.company_id)
        rows.append(
            {
                "registration_id": registration.pk,
                "reference": registration.reference,
                "company_name": registration.company.name,
                "original_submitted_at": registration.original_submitted_at,
                "current_project": str(scopes[registration.opportunity_scope_id]),
                "current_rank": current[registration.pk],
            }
        )
    moving = Registration.objects.filter(opportunity_scope_id=source_id).exclude(
        status__in=CLOSED_STATUSES
    )
    return {
        "rows": rows,
        "deals_moving": moving.count(),
        "decided_prices": RegistrationCategoryApproval.objects.filter(registration__in=moving)
        .exclude(status=RegistrationCategoryApproval.Status.PENDING)
        .count(),
        "same_end_user": scopes[source_id].opportunity.end_user_id
        == scopes[target_id].opportunity.end_user_id,
        "target_project_status": scopes[target_id].opportunity.get_project_status_display(),
    }


def _reopen_prices(registration, actor):
    """Send decided prices back to review. The event history keeps what they were."""
    reopened = []
    approvals = registration.category_approvals.exclude(
        status=RegistrationCategoryApproval.Status.PENDING
    )
    for approval in approvals:
        ended = approval.valid_until.isoformat() if approval.valid_until else "no date"
        reopened.append(f"{approval.category} ({approval.get_status_display()}, until {ended})")
        approval.item_approvals.all().delete()
        approval.renewals.filter(status=PriceApprovalRenewal.Status.PENDING).update(
            status=PriceApprovalRenewal.Status.REJECTED,
            decided_by=actor,
            decided_at=timezone.now(),
            decision_reason="The price went back to DBGI for review.",
        )
        approval.status = RegistrationCategoryApproval.Status.PENDING
        approval.rationale = ""
        approval.reviewed_by = None
        approval.reviewed_at = None
        approval.valid_until = None
        approval.expiry_reminder_sent_at = None
        approval.version += 1
        approval.save()
    return reopened


def _prices_text(reopened):
    if not reopened:
        return ""
    return f" Prices sent back for review: {', '.join(reopened)}."


@transaction.atomic
def merge_projects(*, source_id, target_id, actor, reason, price_action, order):
    preview = merge_preview(source_id, target_id)
    scopes = _active_scopes(source_id, target_id)
    default_order = [row["registration_id"] for row in preview["rows"]]
    if order and (len(order) != len(default_order) or set(order) != set(default_order)):
        raise ProjectChangeError(
            "invalid_order", "List every company in the merged ranking exactly once."
        )
    source, target = scopes[source_id], scopes[target_id]
    change = ProjectChange.objects.create(
        kind=ProjectChange.Kind.MERGE,
        source_scope=source,
        target_scope=target,
        reason=reason,
        price_action=price_action,
        # Stored only when DBGI changed the order; otherwise submission times keep deciding it.
        rank_order=order if order and order != default_order else [],
        previous_ranks=[
            {
                "registration_id": row["registration_id"],
                "project": row["current_project"],
                "rank": row["current_rank"],
            }
            for row in preview["rows"]
        ],
        decided_by=actor,
    )
    registrations = list(
        Registration.objects.select_for_update()
        .filter(opportunity_scope_id=source_id)
        .exclude(status__in=CLOSED_STATUSES)
        .select_related("company")
    )
    for registration in registrations:
        prior_snapshot = registration_snapshot(registration)
        reopened = (
            _reopen_prices(registration, actor)
            if price_action == ProjectChange.PriceAction.REVIEW
            else []
        )
        registration.opportunity_scope = target
        registration.version += 1
        registration.save(update_fields=["opportunity_scope", "version", "updated_at"])
        RegistrationEvent.objects.create(
            registration=registration,
            actor=actor,
            event_type=MERGED_EVENT,
            details=(
                "DBGI combined this project with another project. Your place in line is shown in "
                f"Rankings.{_prices_text(reopened)}{REASON_MARK}{reason} "
                f"Moved from {source} to {target}."
            ),
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        notify_company_users(
            registration=registration,
            event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
            event_key=f"project-change:{change.pk}:{registration.pk}",
            title="Project combined",
            message=(
                f"DBGI combined the project of {registration.reference} with another project. "
                "Open Rankings to see your place in line."
            ),
        )
    source.is_active = False
    source.save(update_fields=["is_active"])
    opportunity = source.opportunity
    if not opportunity.scopes.filter(is_active=True).exists():
        opportunity.is_active = False
        opportunity.save(update_fields=["is_active"])
    return change


def _lot_scope(source_scope, target_scope_id, new_lot_name):
    """The scope that receives the moved products: an active one on this project, or a new lot."""
    name = " ".join(new_lot_name.split())
    if bool(target_scope_id) == bool(name):
        raise ProjectChangeError(
            "invalid_target", "Choose an existing lot or type a new lot name, not both."
        )
    if name:
        opportunity = source_scope.opportunity
        if opportunity.scopes.filter(name__iexact=name).exists():
            raise ProjectChangeError("duplicate_lot", "This project already has a lot named that.")
        return OpportunityScope.objects.create(
            opportunity=opportunity, name=name, scope_type=OpportunityScope.ScopeType.LOT
        )
    target = OpportunityScope.objects.filter(
        pk=target_scope_id, opportunity_id=source_scope.opportunity_id, is_active=True
    ).first()
    if target is None or target.pk == source_scope.pk:
        raise ProjectChangeError("invalid_target", "Choose a different lot on this project.")
    return target


def _copy_attachments(source, new_registration):
    for attachment in source.attachments.all():
        # A separate file: deleting an attachment removes its stored file.
        with attachment.file.open("rb") as stored:
            content = stored.read()
        copy = RegistrationAttachment(
            registration=new_registration,
            original_name=attachment.original_name,
            description=attachment.description,
            uploaded_by=attachment.uploaded_by,
        )
        copy.file.save(attachment.original_name, ContentFile(content), save=False)
        copy.save()


def _move_price_decisions(source, new_registration, moved_items):
    categories = {item.product.category for item in moved_items if item.product_id}
    remaining = {
        item.product.category for item in source.items.select_related("product") if item.product_id
    }
    moved_ids = {item.pk for item in moved_items}
    for approval in source.category_approvals.filter(category__in=categories):
        if approval.category not in remaining:
            approval.registration = new_registration
            approval.save(update_fields=["registration", "updated_at"])
            continue
        # Both deals keep products of this category, so each gets its own decision.
        moved_prices = approval.item_approvals.filter(registration_item_id__in=moved_ids)
        copy = RegistrationCategoryApproval.objects.create(
            registration=new_registration,
            category=approval.category,
            status=approval.status,
            rationale=approval.rationale,
            reviewed_by=approval.reviewed_by,
            reviewed_at=approval.reviewed_at,
            valid_until=approval.valid_until,
            expiry_reminder_sent_at=approval.expiry_reminder_sent_at,
        )
        moved_prices.update(category_approval=copy)


@transaction.atomic
def split_deal(
    *, registration_id, item_ids, target_scope_id, new_lot_name, actor, reason, price_action
):
    source = Registration.objects.select_for_update().get(pk=registration_id)
    if source.status not in SPLITTABLE_STATUSES or not source.opportunity_scope_id:
        raise ProjectChangeError(
            "invalid_transition", "Only a deal DBGI linked to a project can be split."
        )
    if source.repeat_orders.filter(status=RepeatOrder.Status.PENDING).exists():
        raise ProjectChangeError(
            "repeat_order_pending", "Decide this deal's waiting repeat orders before splitting it."
        )
    all_items = set(source.items.values_list("pk", flat=True))
    wanted = set(item_ids)
    if not wanted or not wanted < all_items:
        raise ProjectChangeError(
            "invalid_items", "Choose some of this deal's products. At least one must stay."
        )
    source_scope = source.opportunity_scope
    target = _lot_scope(source_scope, target_scope_id, new_lot_name)
    prior_snapshot = registration_snapshot(source)
    new_registration = Registration.objects.create(
        company=source.company,
        submitted_by=source.submitted_by,
        end_user=source.end_user,
        end_user_name=source.end_user_name,
        end_user_address=source.end_user_address,
        project_title=source.project_title,
        bid_date=source.bid_date,
        delivery_date=source.delivery_date,
        contact_person=source.contact_person,
        contact_designation=source.contact_designation,
        contact_email=source.contact_email,
        contact_number=source.contact_number,
        evidence_description=source.evidence_description,
        evidence_url=source.evidence_url,
        evidence_sharing_confirmed=source.evidence_sharing_confirmed,
        status=source.status,
        needs_review=source.needs_review,
        opportunity_scope=target,
        original_submitted_at=source.original_submitted_at,
    )
    for competitor in source.competitor_items.all():
        competitor.pk = None
        competitor.registration = new_registration
        competitor.save()
    _copy_attachments(source, new_registration)
    moved_items = list(
        RegistrationItem.objects.select_related("product").filter(
            registration=source, pk__in=wanted
        )
    )
    RegistrationItem.objects.filter(pk__in=wanted).update(registration=new_registration)
    _move_price_decisions(source, new_registration, moved_items)
    reopened = []
    if price_action == ProjectChange.PriceAction.REVIEW:
        reopened = _reopen_prices(source, actor) + _reopen_prices(new_registration, actor)
    source.version += 1
    source.save(update_fields=["version", "updated_at"])
    change = ProjectChange.objects.create(
        kind=ProjectChange.Kind.SPLIT,
        source_scope=source_scope,
        target_scope=target,
        source_registration=source,
        new_registration=new_registration,
        reason=reason,
        price_action=price_action,
        decided_by=actor,
    )
    product_names = ", ".join(
        item.product.name if item.product_id else item.non_catalog_name for item in moved_items
    )
    shared = f"{_prices_text(reopened)}{REASON_MARK}{reason} Lot: {target}."
    RegistrationEvent.objects.create(
        registration=source,
        actor=actor,
        event_type=SPLIT_EVENT,
        details=(
            f"DBGI split this deal. {product_names} moved to {new_registration.reference}. "
            f"Your original submission time stays the same.{shared}"
        ),
        snapshot=prior_snapshot,
        resulting_snapshot=registration_snapshot(source),
    )
    RegistrationEvent.objects.create(
        registration=new_registration,
        actor=actor,
        event_type=SPLIT_EVENT,
        details=(
            f"DBGI split this deal from {source.reference}. It keeps the original submission "
            f"time.{shared}"
        ),
        snapshot=registration_snapshot(new_registration),
    )
    notify_company_users(
        registration=new_registration,
        event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        event_key=f"project-change:{change.pk}:{new_registration.pk}",
        title="Deal split",
        message=(
            f"DBGI split {source.reference}. Some products moved to {new_registration.reference}, "
            "which keeps the original submission time."
        ),
    )
    return new_registration
