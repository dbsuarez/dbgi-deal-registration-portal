import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Field, Form, NinjaAPI, Schema, Status, UploadedFile
from ninja.errors import AuthenticationError
from ninja.errors import ValidationError as NinjaValidationError
from ninja.security import django_auth

from .audit import material_changes, registration_change_details, registration_snapshot
from .matching import generate_matching_suggestion
from .models import (
    CompetitorBrand,
    CompetitorBrandAlias,
    CompetitorItem,
    CompetitorModel,
    EndUser,
    EndUserClassificationOption,
    GeographicArea,
    GeographicDataset,
    Opportunity,
    OpportunityScope,
    PortalSetting,
    PriceApprovalRenewal,
    Product,
    ProductPrice,
    ProjectOutcomeReport,
    RankingTieDecision,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationItemApproval,
    RegistrationNotification,
    RegistrationReviewDecision,
    RepeatOrder,
    RepeatOrderLine,
    normalize_end_user_value,
)
from .notifications import (
    notify_company_users,
    notify_dbgi_renewal_requested,
    notify_dbgi_repeat_order_requested,
    notify_dbgi_review_needed,
    notify_dbgi_withdrawal,
    notify_outcome_decision,
    notify_outcome_reported,
    notify_price_decision,
    notify_registration_decision,
    notify_repeat_order_decision,
    notify_submission,
)
from .project_changes import (
    PROJECT_CHANGE_EVENTS,
    SPLITTABLE_STATUSES,
    ProjectChangeError,
    merge_preview,
    merge_projects,
    public_details,
    split_deal,
)
from .ranking import latest_rank_orders, latest_tie_decisions, rank_scope, ranked_registrations
from .working_days import add_working_days

api = NinjaAPI(
    title="DBGI Project Registration API",
    version="1.0.0",
    openapi_url="/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    urls_namespace="dbgi-api",
)


class ErrorDetail(Schema):
    field: str | None = None
    message: str


class ErrorResponse(Schema):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class CompetitorInput(Schema):
    brand: str = Field(min_length=1, max_length=160)
    item_name: str = Field(min_length=1, max_length=200)
    bid_price: Decimal = Field(ge=0)
    remarks: str = ""


class RegistrationItemInput(Schema):
    product_id: int | None = None
    non_catalog_name: str = ""
    quantity: int = Field(ge=1)
    requested_unit_price: Decimal = Field(ge=0)
    justification: str = ""


class RegistrationInput(Schema):
    end_user_id: int
    project_title: str
    bid_date: date
    delivery_date: date
    contact_person: str
    contact_designation: str
    contact_email: str
    contact_number: str
    evidence_description: str
    evidence_url: str = ""
    evidence_sharing_confirmed: bool
    competitor_items: list[CompetitorInput]
    items: list[RegistrationItemInput]


class RegistrationTestPresetInput(Schema):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=240)
    payload: RegistrationInput


class RegistrationTestPresetOutput(Schema):
    id: int
    name: str
    description: str
    payload: dict
    created_by_name: str
    updated_at: datetime

    @staticmethod
    def resolve_created_by_name(obj):
        return obj.owner.get_full_name() or obj.owner.username


class RegistrationUpdate(RegistrationInput):
    version: int
    request_repricing: bool = False


class CatalogNewProductInput(Schema):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=240)
    category: str = Field(min_length=1, max_length=120)
    list_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class CatalogLinkInput(Schema):
    version: int
    reason: str = Field(min_length=5, max_length=1000)
    product_id: int | None = None
    new_product: CatalogNewProductInput | None = None


class RegistrationRepriceInput(Schema):
    version: int
    reason: str = Field(min_length=5, max_length=1000)


class RegistrationFinalize(Schema):
    version: int


class RegistrationWithdrawInput(Schema):
    version: int
    reason: str = Field(min_length=5, max_length=1000)


class OutcomeReportInput(Schema):
    outcome: Literal["won", "lost", "cancelled"]
    note: str = Field(min_length=5, max_length=2000)


class OutcomeDecisionInput(Schema):
    confirm: bool
    note: str = Field(min_length=5, max_length=2000)


class OutcomeReportOutput(Schema):
    id: int
    outcome: str
    outcome_label: str
    note: str
    status: str
    status_label: str
    reported_by_name: str
    created_at: datetime
    decided_by_name: str | None
    decided_at: datetime | None
    decision_note: str


class RegistrationListItem(Schema):
    id: int
    reference: str
    project_title: str
    company_name: str
    end_user_name: str
    end_user_id: int | None
    end_user_status: str | None
    end_user_status_label: str | None
    status: str
    status_label: str
    project_status: str | None
    project_status_label: str
    price_status: str
    price_status_label: str
    total_requested_value: Decimal
    bid_date: date
    age_days: int
    needs_review: bool
    created_at: datetime
    version: int


class RegistrationListResponse(Schema):
    items: list[RegistrationListItem]
    total: int
    page: int
    page_size: int
    grand_total: Decimal


class CompetitorOutput(CompetitorInput):
    id: int


class RegistrationItemOutput(RegistrationItemInput):
    id: int
    product_code: str | None
    product_name: str | None
    display_name: str
    currency: str
    list_unit_price: Decimal
    price_basis: str
    price_basis_label: str
    price_captured_at: datetime
    requested_discount_percent: Decimal | None
    requested_total: Decimal
    approved_unit_price: Decimal | None


class CategoryApprovalOutput(Schema):
    id: int
    category: str
    status: str
    status_label: str
    rationale: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    valid_until: date | None
    version: int
    can_request_renewal: bool
    pending_renewal_id: int | None
    pending_renewal_reason: str | None


class CategoryApprovalDecisionInput(Schema):
    version: int
    status: Literal["changes_requested", "partially_approved", "approved", "rejected"]
    rationale: str = Field(min_length=5, max_length=2000)
    valid_until: date | None = None
    approved_prices: dict[int, Decimal] = Field(default_factory=dict)


class RenewalRequestInput(Schema):
    reason: str = Field(min_length=5, max_length=2000)


class RenewalDecisionInput(Schema):
    approve: bool
    reason: str = Field(min_length=5, max_length=2000)


class ProjectStatusInput(Schema):
    status: Literal["upcoming", "active", "won", "lost", "cancelled", "on_hold"]
    reason: str = Field(min_length=5, max_length=2000)


class AttachmentOutput(Schema):
    id: int
    original_name: str
    description: str
    uploaded_at: datetime
    download_url: str


class EventChangeOutput(Schema):
    label: str
    previous: str
    current: str


class EventOutput(Schema):
    id: int
    event_type: str
    details: str
    actor_name: str
    created_at: datetime
    changes: list[EventChangeOutput]


class MatchingSuggestionOutput(Schema):
    id: int
    outcome: str
    outcome_label: str
    confidence: str
    confidence_label: str
    score: int
    supporting_factors: list[str]
    conflicting_factors: list[str]
    rule_version: str
    candidate_scope_id: int | None
    candidate_scope_label: str | None
    created_at: datetime


class RepeatOrderLineOutput(Schema):
    product_name: str
    quantity: int
    approved_unit_price: Decimal
    line_total: Decimal


class RepeatOrderOutput(Schema):
    id: int
    status: str
    status_label: str
    requested_by: str
    requested_at: datetime
    note: str
    noa_name: str
    noa_url: str
    ntp_name: str
    ntp_url: str
    lines: list[RepeatOrderLineOutput]
    total: Decimal
    can_decide: bool
    decision_reason: str
    decided_by: str | None
    decided_at: datetime | None


class RepeatOrderChoice(Schema):
    item_id: int
    product_name: str
    approved_unit_price: Decimal
    valid_until: date | None


class RepeatOrderDecisionInput(Schema):
    accept: bool
    reason: str = Field(min_length=5, max_length=2000)


class MergePreviewRow(Schema):
    registration_id: int
    reference: str
    company_name: str
    original_submitted_at: datetime
    current_project: str
    current_rank: int


class MergePreviewOutput(Schema):
    rows: list[MergePreviewRow]
    deals_moving: int
    decided_prices: int
    same_end_user: bool
    target_project_status: str


class MergeInput(Schema):
    target_scope_id: int
    reason: str = Field(min_length=5, max_length=2000)
    price_action: Literal["keep", "review"]
    order: list[int] = Field(default_factory=list)


class SplitInput(Schema):
    item_ids: list[int] = Field(min_length=1)
    target_scope_id: int | None = None
    new_lot_name: str = Field(default="", max_length=180)
    reason: str = Field(min_length=5, max_length=2000)
    price_action: Literal["keep", "review"]


class SplitOutput(Schema):
    id: int
    reference: str


class ProjectChangeOutput(Schema):
    id: int
    decided_at: datetime


class RegistrationDetail(RegistrationListItem):
    can_split: bool
    repeat_orders: list[RepeatOrderOutput]
    repeat_order_choices: list[RepeatOrderChoice]
    end_user_address: str
    bid_date: date
    delivery_date: date
    contact_person: str
    contact_designation: str
    contact_email: str
    contact_number: str
    evidence_description: str
    evidence_url: str
    evidence_sharing_confirmed: bool
    can_edit: bool
    can_withdraw: bool
    can_report_outcome: bool
    can_reprice: bool
    outcome_reports: list[OutcomeReportOutput]
    competitor_items: list[CompetitorOutput]
    items: list[RegistrationItemOutput]
    attachments: list[AttachmentOutput]
    events: list[EventOutput]
    opportunity_scope_id: int | None
    opportunity_scope_label: str | None
    matching_suggestion: MatchingSuggestionOutput | None
    category_approvals: list[CategoryApprovalOutput]


class ProductOption(Schema):
    id: int
    code: str
    name: str
    category: str
    currency: str
    list_price: Decimal


class CompetitorModelOption(Schema):
    brand: str
    item_name: str


class GeographicAreaOutput(Schema):
    code: str
    name: str
    level: str
    area_type: str
    postal_code: str


class GeographicDatasetOutput(Schema):
    version: str
    source_url: str
    imported_at: datetime


class EndUserClassificationOptionOutput(Schema):
    name: str
    status: str


class EndUserOutput(Schema):
    id: int
    official_name: str
    acronym: str
    full_address: str
    government_branch: str
    organization_type: str
    sector: str
    region: str
    province: str
    city_municipality: str
    street_address: str
    postal_code: str
    philgeps_reference: str
    source_url: str
    status: str
    status_label: str


class EndUserCreateInput(Schema):
    official_name: str = Field(min_length=2, max_length=240)
    acronym: str = Field(default="", max_length=80)
    government_branch: str = Field(default="", max_length=120)
    organization_type: str = Field(default="", max_length=160)
    sector: str = Field(default="", max_length=160)
    region: str = Field(default="", max_length=160)
    province: str = Field(default="", max_length=160)
    city_municipality: str = Field(min_length=2, max_length=160)
    street_address: str = Field(min_length=2)
    postal_code: str = Field(default="", max_length=20)
    philgeps_reference: str = Field(default="", max_length=120)
    source_url: str = ""


class SessionResponse(Schema):
    username: str
    display_name: str
    email: str
    designation: str
    phone_number: str
    is_dbgi_admin: bool
    is_debug: bool
    one_working_day_ends: date
    end_user_field_help_available: bool
    show_end_user_field_help: bool
    csrf_token: str


class EndUserFieldHelpPreferenceInput(Schema):
    show_end_user_field_help: bool


class EndUserFieldHelpPreferenceOutput(Schema):
    show_end_user_field_help: bool


class ReviewDecisionInput(Schema):
    version: int
    decision: Literal["start_review", "request_changes", "confirm_match", "reject"]
    rationale: str = Field(min_length=5, max_length=2000)
    opportunity_scope_id: int | None = None
    create_new_opportunity: bool = False


class OpportunityScopeOutput(Schema):
    id: int
    opportunity_id: int
    opportunity_title: str
    name: str
    scope_type: str
    label: str


class TieDecisionInput(Schema):
    order: list[int] = Field(min_length=2)
    reason: str = Field(min_length=5, max_length=2000)


class TieDecisionOutput(Schema):
    id: int
    decided_at: datetime


class RankingEntryOutput(Schema):
    rank: int
    is_tied: bool
    tie_decided: bool
    tie_reason: str | None
    registration_id: int
    reference: str
    company_name: str
    project_title: str
    original_submitted_at: datetime


class OpportunityRankingOutput(Schema):
    opportunity_id: int
    opportunity_title: str
    end_user_name: str
    scope_id: int
    scope_name: str
    scope_type: str
    participant_count: int
    entries: list[RankingEntryOutput]


class OpportunityRankingPage(Schema):
    items: list[OpportunityRankingOutput]
    total: int
    page: int
    page_size: int


class NotificationOutput(Schema):
    id: int
    registration_id: int
    registration_reference: str
    event_type: str
    event_type_label: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationPage(Schema):
    items: list[NotificationOutput]
    total: int
    unread_count: int
    page: int
    page_size: int


@api.exception_handler(AuthenticationError)
def authentication_error(request, exc):
    return api.create_response(
        request,
        {"code": "authentication_required", "message": "Sign in to continue.", "details": []},
        status=401,
    )


@api.exception_handler(NinjaValidationError)
def validation_error(request, exc):
    details = [
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors
    ]
    return api.create_response(
        request,
        {
            "code": "validation_error",
            "message": "Correct the highlighted fields.",
            "details": details,
        },
        status=422,
    )


@api.get("/session", auth=django_auth, response=SessionResponse)
def session(request):
    help_available = (
        PortalSetting.objects.filter(key="portal")
        .values_list("show_end_user_field_help", flat=True)
        .first()
    )
    help_available = True if help_available is None else help_available
    return {
        "username": request.user.username,
        "display_name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "designation": request.user.designation,
        "phone_number": request.user.phone_number,
        "is_dbgi_admin": request.user.is_dbgi_admin,
        "is_debug": settings.DEBUG,
        "one_working_day_ends": add_working_days(timezone.now(), 1),
        "end_user_field_help_available": help_available,
        "show_end_user_field_help": help_available and request.user.show_end_user_field_help,
        "csrf_token": get_token(request),
    }


@api.put(
    "/session/preferences/end-user-field-help",
    auth=django_auth,
    response=EndUserFieldHelpPreferenceOutput,
)
def update_end_user_field_help_preference(
    request,
    payload: EndUserFieldHelpPreferenceInput,
):
    request.user.show_end_user_field_help = payload.show_end_user_field_help
    request.user.save(update_fields=["show_end_user_field_help"])
    help_available = (
        PortalSetting.objects.filter(key="portal")
        .values_list("show_end_user_field_help", flat=True)
        .first()
    )
    return {
        "show_end_user_field_help": (
            (True if help_available is None else help_available)
            and request.user.show_end_user_field_help
        )
    }


@api.post("/session/logout", auth=django_auth, response={204: None})
def logout_session(request):
    django_logout(request)
    return Status(204, None)


def _require_debug_mode():
    if not settings.DEBUG:
        raise Http404


def _test_preset_payload(payload):
    return payload.model_dump(mode="json")


@api.get(
    "/development/registration-test-presets",
    auth=django_auth,
    response=list[RegistrationTestPresetOutput],
)
def list_registration_test_presets(request):
    _require_debug_mode()
    from devtools.models import RegistrationTestPreset

    return RegistrationTestPreset.objects.select_related("owner")


@api.post(
    "/development/registration-test-presets",
    auth=django_auth,
    response={201: RegistrationTestPresetOutput, 409: ErrorResponse},
)
def create_registration_test_preset(request, payload: RegistrationTestPresetInput):
    _require_debug_mode()
    from devtools.models import RegistrationTestPreset

    try:
        preset = RegistrationTestPreset.objects.create(
            owner=request.user,
            name=" ".join(payload.name.split()),
            description=" ".join(payload.description.split()),
            payload=_test_preset_payload(payload.payload),
        )
    except IntegrityError:
        return Status(
            409,
            {
                "code": "duplicate_test_preset",
                "message": "You already have test data with this name.",
            },
        )
    return Status(201, preset)


@api.put(
    "/development/registration-test-presets/{preset_id}",
    auth=django_auth,
    response={200: RegistrationTestPresetOutput, 409: ErrorResponse},
)
def update_registration_test_preset(request, preset_id: int, payload: RegistrationTestPresetInput):
    _require_debug_mode()
    from devtools.models import RegistrationTestPreset

    preset = get_object_or_404(RegistrationTestPreset.objects.select_related("owner"), pk=preset_id)
    preset.name = " ".join(payload.name.split())
    preset.description = " ".join(payload.description.split())
    preset.payload = _test_preset_payload(payload.payload)
    try:
        preset.save()
    except IntegrityError:
        return Status(
            409,
            {
                "code": "duplicate_test_preset",
                "message": "The creator of this test data already has test data with this name.",
            },
        )
    return preset


@api.delete(
    "/development/registration-test-presets/{preset_id}",
    auth=django_auth,
    response={204: None},
)
def delete_registration_test_preset(request, preset_id: int):
    _require_debug_mode()
    from devtools.models import RegistrationTestPreset

    preset = get_object_or_404(RegistrationTestPreset, pk=preset_id)
    preset.delete()
    return Status(204, None)


def _serialize_notification(notification):
    return {
        "id": notification.pk,
        "registration_id": notification.registration_id,
        "registration_reference": notification.registration.reference,
        "event_type": notification.event_type,
        "event_type_label": notification.get_event_type_display(),
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.read_at is not None,
        "created_at": notification.created_at,
    }


@api.get(
    "/notifications",
    auth=django_auth,
    response={200: NotificationPage, 400: ErrorResponse},
)
def list_notifications(request, page: int = 1, page_size: int = 25):
    if page < 1 or page_size < 1 or page_size > 100:
        return Status(
            400,
            {
                "code": "invalid_pagination",
                "message": "Page must be at least 1 and page size must be between 1 and 100.",
            },
        )
    queryset = RegistrationNotification.objects.filter(recipient=request.user).select_related(
        "registration"
    )
    total = queryset.count()
    unread_count = queryset.filter(read_at__isnull=True).count()
    start = (page - 1) * page_size
    return {
        "items": [_serialize_notification(item) for item in queryset[start : start + page_size]],
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@api.post(
    "/notifications/{notification_id}/read",
    auth=django_auth,
    response={200: NotificationOutput, 404: ErrorResponse},
)
def mark_notification_read(request, notification_id: int):
    notification = get_object_or_404(
        RegistrationNotification.objects.select_related("registration"),
        pk=notification_id,
        recipient=request.user,
    )
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return _serialize_notification(notification)


def _company_id(user):
    if user.is_dbgi_admin:
        return None
    if user.role != user.Role.COMPANY or not user.company_id or not user.company.is_active:
        return False
    return user.company_id


def _registration_queryset(user):
    company_id = _company_id(user)
    queryset = Registration.objects.select_related(
        "company", "submitted_by", "end_user", "opportunity_scope__opportunity"
    ).prefetch_related("items__product", "items__price_approval", "category_approvals")
    if company_id is False:
        return queryset.none()
    if company_id is not None:
        queryset = queryset.filter(company_id=company_id)
    return queryset


def _serialize_registration(registration):
    total_requested_value = sum(
        (item.requested_total for item in registration.items.all()), Decimal("0.00")
    )
    return {
        "id": registration.pk,
        "reference": registration.reference,
        "project_title": registration.project_title,
        "company_name": registration.company.name,
        "end_user_name": registration.end_user_name,
        "end_user_id": registration.end_user_id,
        "end_user_status": registration.end_user.status if registration.end_user_id else None,
        "end_user_status_label": (
            registration.end_user.get_status_display() if registration.end_user_id else None
        ),
        "status": registration.status,
        "status_label": registration.get_status_display(),
        "project_status": registration.project_status,
        "project_status_label": registration.project_status_label,
        "price_status": registration.price_status,
        "price_status_label": registration.price_status_label,
        "total_requested_value": total_requested_value,
        "bid_date": registration.bid_date,
        "age_days": max((timezone.localdate() - registration.created_at.date()).days, 0),
        "needs_review": registration.needs_review,
        "created_at": registration.created_at,
        "version": registration.version,
    }


def _serialize_registration_event(event, *, include_internal_details):
    if not include_internal_details and event.event_type == "Start review":
        return None
    details = event.details
    if not include_internal_details and event.event_type in {
        "Automatically matched",
        "Confirm eligible match",
    }:
        details = "DBGI confirmed this registration's opportunity match."
    if not include_internal_details and event.event_type in PROJECT_CHANGE_EVENTS:
        details = public_details(details)
    return {
        "id": event.pk,
        "event_type": event.event_type,
        "details": details,
        "actor_name": (
            (event.actor.get_full_name() or event.actor.username) if event.actor_id else "System"
        ),
        "created_at": event.created_at,
        "changes": registration_change_details(event.snapshot, event.resulting_snapshot),
    }


# A partner may report an outcome only while the linked project is still open.
OPEN_PROJECT_STATUSES = {
    Opportunity.ProjectStatus.UPCOMING,
    Opportunity.ProjectStatus.ACTIVE,
    Opportunity.ProjectStatus.ON_HOLD,
}
OUTCOME_REPORTABLE_STATUSES = {Registration.Status.ELIGIBLE_MATCHED}


ACTIVE_PRICE_STATUSES = {
    RegistrationCategoryApproval.Status.APPROVED,
    RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
}


def _item_label(item):
    return item.product.name if item.product_id else item.non_catalog_name


def _has_active_price(item):
    price = getattr(item, "price_approval", None)
    return (
        price is not None
        and price.approved_unit_price is not None
        and price.category_approval.effective_status in ACTIVE_PRICE_STATUSES
    )


def _repeat_order_choices(registration):
    """Products a repeat order can use: decided, valid, on a deal DBGI confirmed (decision D1)."""
    if registration.status not in OUTCOME_REPORTABLE_STATUSES:
        return []
    items = registration.items.select_related("product", "price_approval__category_approval")
    return [
        {
            "item_id": item.pk,
            "product_name": _item_label(item),
            "approved_unit_price": item.price_approval.approved_unit_price,
            "valid_until": item.price_approval.category_approval.valid_until,
        }
        for item in items
        if _has_active_price(item)
    ]


def _serialize_repeat_order(repeat_order, user):
    lines = [
        {
            "product_name": _item_label(line.registration_item),
            "quantity": line.quantity,
            "approved_unit_price": line.approved_unit_price,
            "line_total": line.quantity * line.approved_unit_price,
        }
        for line in repeat_order.lines.select_related("registration_item__product")
    ]
    return {
        "id": repeat_order.pk,
        "status": repeat_order.status,
        "status_label": repeat_order.get_status_display(),
        "requested_by": (
            repeat_order.requested_by.get_full_name() or repeat_order.requested_by.username
        ),
        "requested_at": repeat_order.requested_at,
        "note": repeat_order.note,
        "noa_name": repeat_order.noa_name,
        "noa_url": f"/attachments/repeat-orders/{repeat_order.pk}/noa/download/",
        "ntp_name": repeat_order.ntp_name,
        "ntp_url": f"/attachments/repeat-orders/{repeat_order.pk}/ntp/download/",
        "lines": lines,
        "total": sum((line["line_total"] for line in lines), Decimal("0.00")),
        "can_decide": user.is_dbgi_admin
        and repeat_order.status == RepeatOrder.Status.PENDING
        and repeat_order.registration.status != Registration.Status.WITHDRAWN,
        "decision_reason": repeat_order.decision_reason,
        "decided_by": (
            (repeat_order.decided_by.get_full_name() or repeat_order.decided_by.username)
            if repeat_order.decided_by_id
            else None
        ),
        "decided_at": repeat_order.decided_at,
    }


def _outcome_report_blocker(registration):
    """Why this registration cannot get an outcome report now (an error dict), or None."""
    if (
        registration.status not in OUTCOME_REPORTABLE_STATUSES
        or not registration.opportunity_scope_id
    ):
        return {
            "code": "invalid_transition",
            "message": "Only a registration DBGI linked to a project can report its outcome.",
        }
    if registration.opportunity_scope.opportunity.project_status not in OPEN_PROJECT_STATUSES:
        return {
            "code": "invalid_transition",
            "message": "This project already has a final outcome.",
        }
    if registration.outcome_reports.filter(status=ProjectOutcomeReport.Status.PENDING).exists():
        return {
            "code": "outcome_report_pending",
            "message": "An outcome report for this registration is already waiting for DBGI.",
        }
    return None


def _serialize_outcome_report(report):
    def name(user):
        return (user.get_full_name() or user.username) if user else None

    return {
        "id": report.pk,
        "outcome": report.outcome,
        "outcome_label": report.get_outcome_display(),
        "note": report.note,
        "status": report.status,
        "status_label": report.get_status_display(),
        "reported_by_name": name(report.reported_by),
        "created_at": report.created_at,
        "decided_by_name": name(report.decided_by),
        "decided_at": report.decided_at,
        "decision_note": report.decision_note,
    }


def _set_project_status(opportunity, status, actor, reason):
    """Change a project's status and record it on every registration linked to the project."""
    old_label = opportunity.get_project_status_display()
    previous_status = opportunity.project_status
    opportunity.project_status = status
    opportunity.update_hold_clock(previous_status)
    opportunity.save(
        update_fields=[
            "project_status",
            "on_hold_since",
            "hold_reminder_sent_at",
            "hold_limit_reached_at",
        ]
    )
    for registration in Registration.objects.filter(opportunity_scope__opportunity=opportunity):
        RegistrationEvent.objects.create(
            registration=registration,
            actor=actor,
            event_type="Project status changed",
            details=(
                f"Project status changed from {old_label} to "
                f"{opportunity.get_project_status_display()}: {reason}"
            ),
            snapshot=registration_snapshot(registration),
        )


def _serialize_registration_detail(registration, user):
    detail = _serialize_registration(registration)
    serialized_events = [
        _serialize_registration_event(event, include_internal_details=user.is_dbgi_admin)
        for event in registration.events.select_related("actor").all()
    ]
    detail.update(
        {
            "end_user_address": registration.end_user_address,
            "bid_date": registration.bid_date,
            "delivery_date": registration.delivery_date,
            "contact_person": registration.contact_person,
            "contact_designation": registration.contact_designation,
            "contact_email": registration.contact_email,
            "contact_number": registration.contact_number,
            "evidence_description": registration.evidence_description,
            "evidence_url": registration.evidence_url,
            "evidence_sharing_confirmed": registration.evidence_sharing_confirmed,
            "can_edit": not user.is_dbgi_admin
            and registration.status != Registration.Status.WITHDRAWN,
            "can_withdraw": not user.is_dbgi_admin
            and registration.status in Registration.WITHDRAWABLE_STATUSES,
            "can_reprice": user.is_dbgi_admin
            and registration.status
            not in {Registration.Status.WITHDRAWN, Registration.Status.REJECTED}
            and not _commercial_review_started(registration),
            "can_report_outcome": not user.is_dbgi_admin
            and _outcome_report_blocker(registration) is None,
            "can_split": user.is_dbgi_admin
            and registration.status in SPLITTABLE_STATUSES
            and registration.opportunity_scope_id is not None
            and registration.items.count() > 1
            and not registration.repeat_orders.filter(status=RepeatOrder.Status.PENDING).exists(),
            "repeat_orders": [
                _serialize_repeat_order(repeat_order, user)
                for repeat_order in registration.repeat_orders.select_related(
                    "requested_by", "decided_by", "registration"
                )
            ],
            "repeat_order_choices": (
                [] if user.is_dbgi_admin else _repeat_order_choices(registration)
            ),
            "outcome_reports": [
                _serialize_outcome_report(report)
                for report in registration.outcome_reports.select_related(
                    "reported_by", "decided_by"
                )
            ],
            "competitor_items": [
                {
                    "id": item.pk,
                    "brand": item.brand,
                    "item_name": item.item_name,
                    "bid_price": item.bid_price,
                    "remarks": item.remarks,
                }
                for item in registration.competitor_items.all()
            ],
            "items": [
                {
                    "id": item.pk,
                    "product_id": item.product_id,
                    "product_code": item.product.code if item.product_id else None,
                    "product_name": item.product.name if item.product_id else None,
                    "non_catalog_name": item.non_catalog_name,
                    "display_name": item.display_name,
                    "quantity": item.quantity,
                    "requested_unit_price": item.requested_unit_price,
                    "currency": item.currency,
                    "list_unit_price": item.list_unit_price_snapshot,
                    "price_basis": item.price_basis,
                    "price_basis_label": item.get_price_basis_display(),
                    "price_captured_at": item.price_captured_at,
                    "requested_discount_percent": item.requested_discount_percent,
                    "requested_total": item.requested_total,
                    "approved_unit_price": (
                        item.price_approval.approved_unit_price
                        if hasattr(item, "price_approval")
                        else None
                    ),
                    "justification": item.justification,
                }
                for item in registration.items.all()
            ],
            "attachments": [
                {
                    "id": attachment.pk,
                    "original_name": attachment.original_name,
                    "description": attachment.description,
                    "uploaded_at": attachment.uploaded_at,
                    "download_url": f"/attachments/{attachment.pk}/download/",
                }
                for attachment in registration.attachments.all()
            ],
            "events": [event for event in serialized_events if event is not None],
            "opportunity_scope_id": registration.opportunity_scope_id,
            "opportunity_scope_label": (
                str(registration.opportunity_scope) if registration.opportunity_scope_id else None
            ),
            "matching_suggestion": (
                _serialize_matching_suggestion(
                    registration.matching_suggestions.filter(is_current=True)
                    .select_related("candidate_scope__opportunity")
                    .first()
                )
                if user.is_dbgi_admin
                else None
            ),
            "category_approvals": [
                _serialize_category_approval(approval)
                for approval in registration.category_approvals.select_related(
                    "reviewed_by", "registration"
                ).all()
            ],
        }
    )
    return detail


def _serialize_matching_suggestion(suggestion):
    if not suggestion:
        return None
    return {
        "id": suggestion.pk,
        "outcome": suggestion.outcome,
        "outcome_label": suggestion.get_outcome_display(),
        "confidence": suggestion.confidence,
        "confidence_label": suggestion.get_confidence_display(),
        "score": suggestion.score,
        "supporting_factors": suggestion.supporting_factors,
        "conflicting_factors": suggestion.conflicting_factors,
        "rule_version": suggestion.rule_version,
        "candidate_scope_id": suggestion.candidate_scope_id,
        "candidate_scope_label": (
            str(suggestion.candidate_scope) if suggestion.candidate_scope_id else None
        ),
        "created_at": suggestion.created_at,
    }


def _serialize_category_approval(approval):
    withdrawn = approval.registration.status == Registration.Status.WITHDRAWN
    pending = (
        None
        if withdrawn
        else approval.renewals.filter(status=PriceApprovalRenewal.Status.PENDING).first()
    )
    return {
        "can_request_renewal": pending is None
        and not withdrawn
        and approval.status
        in {
            RegistrationCategoryApproval.Status.APPROVED,
            RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
        },
        "pending_renewal_id": pending.pk if pending else None,
        "pending_renewal_reason": pending.reason if pending else None,
        "id": approval.pk,
        "category": approval.category,
        "status": approval.effective_status,
        "status_label": RegistrationCategoryApproval.Status(approval.effective_status).label,
        "rationale": approval.rationale,
        "reviewed_by": (
            approval.reviewed_by.get_full_name() or approval.reviewed_by.username
            if approval.reviewed_by_id
            else None
        ),
        "reviewed_at": approval.reviewed_at,
        "valid_until": approval.valid_until,
        "version": approval.version,
    }


def _require_admin(request):
    return request.user.is_dbgi_admin


def _serialize_end_user(end_user):
    return {
        "id": end_user.pk,
        "official_name": end_user.official_name,
        "acronym": end_user.acronym,
        "full_address": end_user.full_address,
        "government_branch": end_user.government_branch,
        "organization_type": end_user.organization_type,
        "sector": end_user.sector,
        "region": end_user.region,
        "province": end_user.province,
        "city_municipality": end_user.city_municipality,
        "street_address": end_user.street_address,
        "postal_code": end_user.postal_code,
        "philgeps_reference": end_user.philgeps_reference,
        "source_url": end_user.source_url,
        "status": end_user.status,
        "status_label": end_user.get_status_display(),
    }


def _visible_end_users(user):
    queryset = EndUser.objects.filter(is_active=True).prefetch_related("aliases")
    if user.is_dbgi_admin:
        return queryset
    company_id = _company_id(user)
    if company_id is False:
        return queryset.none()
    return queryset.filter(
        Q(status=EndUser.Status.VERIFIED)
        | Q(status=EndUser.Status.PENDING, proposed_by_company_id=company_id)
    )


@api.get("/end-users", auth=django_auth, response=list[EndUserOutput])
def list_end_users(request, search: str = ""):
    queryset = _visible_end_users(request.user)
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(
            Q(official_name__icontains=term)
            | Q(acronym__icontains=term)
            | Q(aliases__name__icontains=term)
            | Q(city_municipality__icontains=term)
            | Q(province__icontains=term)
        ).distinct()
    return [_serialize_end_user(item) for item in queryset.order_by("official_name")[:100]]


@api.get(
    "/end-user-classifications",
    auth=django_auth,
    response=list[EndUserClassificationOptionOutput],
)
def list_end_user_classifications(
    request,
    category: Literal["organization_type", "sector"],
):
    queryset = EndUserClassificationOption.objects.filter(category=category, is_active=True)
    if not request.user.is_dbgi_admin:
        company_id = _company_id(request.user)
        if company_id is False:
            return []
        queryset = queryset.filter(
            Q(status=EndUserClassificationOption.Status.APPROVED)
            | Q(
                status=EndUserClassificationOption.Status.PENDING,
                proposed_by_company_id=company_id,
            )
        )
    return queryset.order_by("name").values("name", "status")


@api.get(
    "/geographic-dataset",
    auth=django_auth,
    response=GeographicDatasetOutput | None,
)
def geographic_dataset(request):
    return GeographicDataset.objects.filter(is_current=True).first()


@api.get(
    "/geographic-areas",
    auth=django_auth,
    response={200: list[GeographicAreaOutput], 400: ErrorResponse},
)
def list_geographic_areas(
    request,
    level: Literal["region", "province", "city_municipality", "barangay"],
    region_code: str = "",
    province_code: str = "",
    city_municipality_code: str = "",
):
    queryset = GeographicArea.objects.filter(level=level, is_active=True)
    if level != GeographicArea.Level.REGION and not region_code:
        return Status(
            400,
            {
                "code": "region_required",
                "message": "Choose a region first.",
            },
        )
    if region_code:
        queryset = queryset.filter(region_code=region_code)
    if province_code:
        queryset = queryset.filter(province_code=province_code)
    if level == GeographicArea.Level.BARANGAY:
        if not city_municipality_code:
            return Status(
                400,
                {
                    "code": "city_municipality_required",
                    "message": "Choose a city or municipality first.",
                },
            )
        queryset = queryset.filter(city_municipality_code=city_municipality_code)
    return queryset.order_by("name", "code")[:5000]


@api.post(
    "/end-users",
    auth=django_auth,
    response={201: EndUserOutput, 400: ErrorResponse, 403: ErrorResponse, 409: ErrorResponse},
)
def create_end_user(request, payload: EndUserCreateInput):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403, {"code": "company_access_required", "message": "A company account is required."}
        )
    if (
        payload.government_branch
        and payload.government_branch not in EndUser.GovernmentBranch.values
    ):
        return Status(
            400,
            {
                "code": "invalid_government_branch",
                "message": "Choose a government branch from the available list.",
            },
        )
    candidate = EndUser(
        **payload.model_dump(),
        proposed_by_company_id=company_id,
        created_by=request.user,
        status=EndUser.Status.PENDING,
    )
    candidate.normalized_name = candidate.official_name
    candidate.normalized_address = candidate.full_address
    try:
        with transaction.atomic():
            candidate.save()
            for category, name in (
                (
                    EndUserClassificationOption.Category.ORGANIZATION_TYPE,
                    candidate.organization_type,
                ),
                (EndUserClassificationOption.Category.SECTOR, candidate.sector),
            ):
                normalized_name = normalize_end_user_value(name)
                if not normalized_name:
                    continue
                EndUserClassificationOption.objects.get_or_create(
                    category=category,
                    normalized_name=normalized_name,
                    defaults={
                        "name": name.strip(),
                        "proposed_by_company_id": company_id,
                        "created_by": request.user,
                    },
                )
    except IntegrityError:
        return Status(
            409,
            {
                "code": "duplicate_end_user",
                "message": "An active End-user with the same name and address already exists.",
            },
        )
    return Status(201, _serialize_end_user(candidate))


def _selected_end_user(user, end_user_id):
    return get_object_or_404(_visible_end_users(user), pk=end_user_id)


@api.get(
    "/registrations",
    auth=django_auth,
    response={200: RegistrationListResponse, 400: ErrorResponse},
)
def list_registrations(
    request,
    page: int = 1,
    page_size: int = 25,
    search: str = "",
    project_status: Literal[
        "", "not_linked", "upcoming", "active", "won", "lost", "cancelled", "on_hold"
    ] = "",
    registration_status: Literal[
        "",
        "submitted",
        "under_review",
        "changes_requested",
        "resubmitted",
        "eligible_matched",
        "review_required",
        "approved",
        "rejected",
        "withdrawn",
    ] = "",
    sort: Literal[
        "created_at",
        "-created_at",
        "project_title",
        "-project_title",
        "end_user_name",
        "-end_user_name",
        "company__name",
        "-company__name",
    ] = "-created_at",
):
    if page < 1 or page_size < 1 or page_size > 100:
        return Status(
            400,
            {
                "code": "invalid_pagination",
                "message": "Page must be at least 1 and page size must be between 1 and 100.",
            },
        )
    queryset = _registration_queryset(request.user)
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(
            Q(project_title__icontains=term)
            | Q(end_user_name__icontains=term)
            | Q(company__name__icontains=term)
        )
    if project_status == "not_linked":
        queryset = queryset.filter(opportunity_scope__isnull=True)
    elif project_status:
        queryset = queryset.filter(opportunity_scope__opportunity__project_status=project_status)
    if registration_status:
        queryset = queryset.filter(status=registration_status)
    total = queryset.count()
    grand_total = RegistrationItem.objects.filter(registration__in=queryset).aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("requested_unit_price"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )
    )["total"] or Decimal("0.00")
    start = (page - 1) * page_size
    records = queryset.order_by(sort)[start : start + page_size]
    return {
        "items": [_serialize_registration(record) for record in records],
        "total": total,
        "page": page,
        "page_size": page_size,
        "grand_total": grand_total,
    }


@api.get(
    "/registrations/{registration_id}",
    auth=django_auth,
    response={200: RegistrationDetail, 404: ErrorResponse},
)
def get_registration(request, registration_id: int):
    registration = get_object_or_404(
        _registration_queryset(request.user).prefetch_related(
            "competitor_items", "items__product", "attachments", "events__actor"
        ),
        pk=registration_id,
    )
    return _serialize_registration_detail(registration, request.user)


@api.get("/products", auth=django_auth, response=list[ProductOption])
def list_products(request, search: str = ""):
    queryset = Product.objects.with_list_price().filter(is_active=True)
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(
            Q(code__icontains=term) | Q(name__icontains=term) | Q(category__icontains=term)
        )
    return queryset.order_by("code")[:100]


@api.get("/competitor-brands", auth=django_auth, response=list[str])
def list_competitor_brands(request):
    return list(
        CompetitorBrand.objects.filter(is_active=True)
        .order_by("name")
        .values_list("name", flat=True)[:100]
    )


@api.get("/competitor-models", auth=django_auth, response=list[CompetitorModelOption])
def list_competitor_models(request):
    queryset = (
        CompetitorModel.objects.filter(is_active=True, brand__is_active=True)
        .select_related("brand")
        .order_by("brand__name", "name")[:500]
    )
    return [
        {"brand": competitor_model.brand.name, "item_name": competitor_model.name}
        for competitor_model in queryset
    ]


def _resolve_competitor_brand(name):
    cleaned = " ".join(name.split())
    normalized = cleaned.casefold()
    brand = CompetitorBrand.objects.filter(normalized_name=normalized).first()
    if brand:
        return brand
    alias = (
        CompetitorBrandAlias.objects.select_related("brand")
        .filter(normalized_name=normalized)
        .first()
    )
    if alias:
        return alias.brand
    brand, _ = CompetitorBrand.objects.get_or_create(
        normalized_name=normalized, defaults={"name": cleaned}
    )
    return brand


def _resolve_competitor_model(brand, name):
    cleaned = " ".join(name.split())
    normalized = cleaned.casefold()
    competitor_model, _ = CompetitorModel.objects.get_or_create(
        brand=brand,
        normalized_name=normalized,
        defaults={"name": cleaned},
    )
    return competitor_model


def _validate_input(payload):
    details = []
    if not payload.competitor_items:
        details.append(
            {"field": "competitor_items", "message": "Add at least one competitor item."}
        )
    if not payload.items:
        details.append({"field": "items", "message": "Add at least one requested product."})
    if not payload.evidence_description.strip():
        details.append(
            {"field": "evidence_description", "message": "Describe the supporting evidence."}
        )
    if not payload.evidence_sharing_confirmed:
        details.append(
            {
                "field": "evidence_sharing_confirmed",
                "message": "Confirm authorization to share the attachment.",
            }
        )
    for index, item in enumerate(payload.items):
        if not item.product_id and not item.non_catalog_name.strip():
            details.append(
                {
                    "field": f"items.{index}",
                    "message": "Choose a catalog product or enter a product description.",
                }
            )
    return details


def _alerts_dbgi_on_attachment_change(registration):
    """On by default, including before the settings record exists. Only a registration DBGI already
    confirmed needs this: on any other open registration, DBGI sees the files when it reviews."""
    if registration.status != Registration.Status.ELIGIBLE_MATCHED:
        return False
    return (
        PortalSetting.objects.filter(key="portal")
        .values_list("alert_dbgi_on_attachment_change", flat=True)
        .first()
        is not False
    )


def _flag_attachment_change(registration):
    if _alerts_dbgi_on_attachment_change(registration):
        registration.needs_review = True
        registration.save(update_fields=["needs_review", "updated_at"])


def _commercial_review_started(registration):
    return registration.category_approvals.exclude(
        status=RegistrationCategoryApproval.Status.PENDING
    ).exists()


def _item_key(product_id, non_catalog_name):
    return (product_id, "" if product_id else normalize_end_user_value(non_catalog_name))


def _requested_items_changed(registration, payload):
    saved = Counter(
        (
            *_item_key(item.product_id, item.non_catalog_name),
            item.quantity,
            item.requested_unit_price,
        )
        for item in registration.items.all()
    )
    sent = Counter(
        (
            *_item_key(item.product_id, item.non_catalog_name),
            item.quantity,
            item.requested_unit_price,
        )
        for item in payload.items
    )
    return saved != sent


def _capture_price(item, product, basis):
    """Record the price in effect now; only new lines and explicit repricing do this."""
    item.list_unit_price_snapshot = product.list_price
    item.price_version_id = product.list_price_id
    item.currency = product.currency
    item.price_basis = basis
    item.price_captured_at = timezone.now()


def _save_children(registration, payload, *, is_edit=False, reprice=False):
    """Save competitor and product lines. A line that stays keeps its captured price, so an edit is
    never a repricing event unless it adds or changes a product, or repricing was asked for."""
    registration.competitor_items.all().delete()
    competitor_rows = []
    for item in payload.competitor_items:
        brand = _resolve_competitor_brand(item.brand)
        competitor_model = _resolve_competitor_model(brand, item.item_name)
        competitor_rows.append(
            CompetitorItem(
                registration=registration,
                brand=brand.name,
                item_name=competitor_model.name,
                bid_price=item.bid_price,
                remarks=item.remarks,
            )
        )
    CompetitorItem.objects.bulk_create(competitor_rows)
    product_ids = {item.product_id for item in payload.items if item.product_id}
    products = {
        product.pk: product
        for product in Product.objects.with_list_price().filter(pk__in=product_ids)
    }
    if len(products) != len(product_ids):
        return False
    remaining = defaultdict(list)
    for existing in registration.items.all():
        remaining[_item_key(existing.product_id, existing.non_catalog_name)].append(existing)
    new_basis = (
        RegistrationItem.PriceBasis.PRODUCT_CHANGED
        if is_edit
        else RegistrationItem.PriceBasis.ORIGINAL
    )
    for item in payload.items:
        product = products.get(item.product_id)
        matches = remaining[_item_key(item.product_id, item.non_catalog_name)]
        if matches:
            line = matches.pop()
            line.non_catalog_name = item.non_catalog_name
            line.quantity = item.quantity
            line.requested_unit_price = item.requested_unit_price
            line.justification = item.justification
            if reprice and product:
                _capture_price(line, product, RegistrationItem.PriceBasis.COMPANY_REQUEST)
        else:
            if product and not product.is_active:
                return False
            line = RegistrationItem(
                registration=registration,
                product=product,
                non_catalog_name=item.non_catalog_name,
                quantity=item.quantity,
                requested_unit_price=item.requested_unit_price,
                justification=item.justification,
            )
            if product:
                _capture_price(line, product, new_basis)
            else:
                line.price_basis = new_basis
        line.save()
    for leftovers in remaining.values():
        for line in leftovers:
            line.delete()
    categories = {
        category
        for category in registration.items.filter(product__isnull=False).values_list(
            "product__category", flat=True
        )
    }
    registration.category_approvals.filter(
        status=RegistrationCategoryApproval.Status.PENDING
    ).exclude(category__in=categories).delete()
    existing_categories = set(registration.category_approvals.values_list("category", flat=True))
    RegistrationCategoryApproval.objects.bulk_create(
        [
            RegistrationCategoryApproval(registration=registration, category=category)
            for category in sorted(categories - existing_categories)
        ]
    )
    return True


@api.post(
    "/registrations",
    auth=django_auth,
    response={201: RegistrationListItem, 400: ErrorResponse, 403: ErrorResponse},
)
def create_registration(request, payload: RegistrationInput):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {
                "code": "company_access_required",
                "message": "A valid company account is required.",
            },
        )
    details = _validate_input(payload)
    if details:
        return Status(
            400,
            {
                "code": "validation_error",
                "message": "Correct the highlighted fields.",
                "details": details,
            },
        )
    end_user = _selected_end_user(request.user, payload.end_user_id)
    values = payload.model_dump(exclude={"competitor_items", "items", "end_user_id"})
    with transaction.atomic():
        registration = Registration.objects.create(
            company_id=company_id,
            submitted_by=request.user,
            end_user=end_user,
            end_user_name=end_user.official_name,
            end_user_address=end_user.full_address,
            needs_review=end_user.status != EndUser.Status.VERIFIED,
            **values,
        )
        if not _save_children(registration, payload):
            transaction.set_rollback(True)
            return Status(
                400,
                {
                    "code": "invalid_product",
                    "message": "One or more selected products are unavailable.",
                },
            )
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Submitted",
            details="Registration submitted.",
            snapshot=registration_snapshot(registration),
        )
        notify_submission(registration)
        notify_dbgi_review_needed(registration, "new registration submitted")
        generate_matching_suggestion(registration)
    return Status(201, _serialize_registration(registration))


@api.put(
    "/registrations/{registration_id}",
    auth=django_auth,
    response={
        200: RegistrationListItem,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def update_registration(request, registration_id: int, payload: RegistrationUpdate):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {
                "code": "company_access_required",
                "message": "A valid company account is required.",
            },
        )
    details = _validate_input(payload)
    if details:
        return Status(
            400,
            {
                "code": "validation_error",
                "message": "Correct the highlighted fields.",
                "details": details,
            },
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update().select_related("company"),
            pk=registration_id,
            company_id=company_id,
        )
        if registration.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": (
                        "This registration changed after you opened it. Refresh before saving."
                    ),
                },
            )
        if registration.status == Registration.Status.WITHDRAWN:
            return Status(409, WITHDRAWN_ERROR)
        if _commercial_review_started(registration) and (
            payload.request_repricing or _requested_items_changed(registration, payload)
        ):
            return Status(
                409,
                {
                    "code": "commercial_review_locked",
                    "message": (
                        "Products and requested prices cannot change after commercial review "
                        "has started. Ask DBGI to request changes first."
                    ),
                },
            )
        prior_snapshot = registration_snapshot(registration)
        end_user = _selected_end_user(request.user, payload.end_user_id)
        end_user_changed = registration.end_user_id != end_user.pk
        for name, value in payload.model_dump(
            exclude={"competitor_items", "items", "version", "end_user_id", "request_repricing"}
        ).items():
            setattr(registration, name, value)
        registration.end_user = end_user
        registration.end_user_name = end_user.official_name
        registration.end_user_address = end_user.full_address
        registration.version += 1
        registration.save()
        if not _save_children(
            registration, payload, is_edit=True, reprice=payload.request_repricing
        ):
            transaction.set_rollback(True)
            return Status(
                400,
                {
                    "code": "invalid_product",
                    "message": "One or more selected products are unavailable.",
                },
            )
        changes = material_changes(prior_snapshot, registration_snapshot(registration))
        if end_user_changed:
            changes.insert(0, "End-user")
        if payload.request_repricing:
            changes.append("Repricing requested")
        previous_status = registration.status
        if registration.status == Registration.Status.CHANGES_REQUESTED:
            registration.status = Registration.Status.RESUBMITTED
            registration.needs_review = True
        elif changes:
            registration.needs_review = True
            if registration.status == Registration.Status.ELIGIBLE_MATCHED:
                registration.status = Registration.Status.REVIEW_REQUIRED
        registration.save()
        if registration.status != previous_status:
            notify_dbgi_review_needed(
                registration,
                "corrections submitted"
                if registration.status == Registration.Status.RESUBMITTED
                else "edited after it was registered",
            )
        if changes:
            event_type = "Company edit"
            details = f"Company changed: {', '.join(changes)}. DBGI review is required."
        elif registration.status != previous_status:
            event_type = "Company edit"
            details = "Company saved the requested corrections. DBGI review is required."
        else:
            event_type = "Administrative correction"
            details = (
                "Company corrected administrative details. "
                "The captured prices, place in line, and status are unchanged."
            )
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type=event_type,
            details=details,
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        if changes or registration.status != previous_status:
            generate_matching_suggestion(registration)
    return _serialize_registration(registration)


@api.get(
    "/rankings",
    auth=django_auth,
    response={200: OpportunityRankingPage, 400: ErrorResponse, 403: ErrorResponse},
)
def list_rankings(request, page: int = 1, page_size: int = 25, search: str = ""):
    if page < 1 or page_size < 1 or page_size > 100:
        return Status(
            400,
            {
                "code": "invalid_pagination",
                "message": "Page must be at least 1 and page size must be between 1 and 100.",
            },
        )
    company_id = _company_id(request.user)
    if company_id is False:
        return Status(
            403,
            {
                "code": "company_access_required",
                "message": "A valid company account is required.",
            },
        )

    scopes = OpportunityScope.objects.filter(
        is_active=True,
        opportunity__is_active=True,
    ).select_related("opportunity")
    if company_id is None:
        scopes = scopes.filter(registrations__status=Registration.Status.ELIGIBLE_MATCHED)
    else:
        scopes = scopes.filter(
            registrations__status=Registration.Status.ELIGIBLE_MATCHED,
            registrations__company_id=company_id,
        )
    if search.strip():
        term = search.strip()
        scopes = scopes.filter(
            Q(opportunity__title__icontains=term)
            | Q(opportunity__end_user_name__icontains=term)
            | Q(name__icontains=term)
        )
    scopes = scopes.distinct().order_by("opportunity__title", "name", "id")
    total = scopes.count()
    start = (page - 1) * page_size
    page_scopes = list(scopes[start : start + page_size])
    scope_ids = [scope.pk for scope in page_scopes]

    registrations_by_scope = ranked_registrations(scope_ids)
    decisions = latest_tie_decisions(scope_ids)
    rank_orders = latest_rank_orders(scope_ids)

    items = []
    for scope in page_scopes:
        ranked = registrations_by_scope[scope.pk]
        entries = []
        for ranked_entry in rank_scope(scope.pk, ranked, decisions, rank_orders.get(scope.pk)):
            registration = ranked_entry.registration
            if company_id is None or registration.company_id == company_id:
                entries.append(
                    {
                        "rank": ranked_entry.rank,
                        "is_tied": ranked_entry.is_tied,
                        "tie_decided": ranked_entry.tie_decision is not None,
                        "tie_reason": (
                            ranked_entry.tie_decision.reason
                            if ranked_entry.tie_decision and company_id is None
                            else None
                        ),
                        "registration_id": registration.pk,
                        "reference": registration.reference,
                        "company_name": registration.company.name,
                        "project_title": registration.project_title,
                        "original_submitted_at": registration.original_submitted_at,
                    }
                )
        items.append(
            {
                "opportunity_id": scope.opportunity_id,
                "opportunity_title": scope.opportunity.title,
                "end_user_name": scope.opportunity.end_user_name,
                "scope_id": scope.pk,
                "scope_name": scope.name,
                "scope_type": scope.scope_type,
                "participant_count": len(ranked),
                "entries": entries,
            }
        )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@api.post(
    "/review/opportunity-scopes/{scope_id}/tie-decision",
    auth=django_auth,
    response={200: TieDecisionOutput, 400: ErrorResponse, 403: ErrorResponse, 404: ErrorResponse},
)
def decide_ranking_tie(request, scope_id: int, payload: TieDecisionInput):
    """DBGI sets the order of registrations with the same submission time (decision B5)."""
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        get_object_or_404(OpportunityScope.objects.select_for_update(), pk=scope_id, is_active=True)
        ranked = ranked_registrations([scope_id])[scope_id]
        by_id = {registration.pk: registration for registration in ranked}
        first = by_id.get(payload.order[0])
        tied_ids = {
            registration.pk
            for registration in ranked
            if first and registration.original_submitted_at == first.original_submitted_at
        }
        if (
            len(tied_ids) < 2
            or len(set(payload.order)) != len(payload.order)
            or set(payload.order) != tied_ids
        ):
            return Status(
                400,
                {
                    "code": "invalid_tie",
                    "message": "List every registration in this tie exactly once.",
                },
            )
        decision = RankingTieDecision.objects.create(
            opportunity_scope_id=scope_id,
            submitted_at=first.original_submitted_at,
            order=payload.order,
            reason=payload.reason.strip(),
            decided_by=request.user,
        )
        decisions = latest_tie_decisions([scope_id])
        rank_order = latest_rank_orders([scope_id]).get(scope_id)
        for entry in rank_scope(scope_id, ranked, decisions, rank_order):
            registration = entry.registration
            if registration.pk not in tied_ids:
                continue
            # The company sees its own result only: the reason may name another company.
            RegistrationEvent.objects.create(
                registration=registration,
                actor=request.user,
                event_type="Tied ranking decided",
                details=f"DBGI decided a tied ranking. This registration is now rank {entry.rank}.",
                snapshot=registration_snapshot(registration),
            )
            notify_company_users(
                registration=registration,
                event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
                event_key=f"tie-decision:{decision.pk}:{registration.pk}",
                title="Tied ranking decided",
                message=(
                    f"DBGI decided a tied ranking for {registration.reference}. "
                    "Open Rankings to see your rank."
                ),
            )
    return {"id": decision.pk, "decided_at": decision.decided_at}


ADMIN_REQUIRED = {"code": "admin_required", "message": "DBGI administrator access is required."}


@api.get(
    "/review/opportunity-scopes/{scope_id}/merge-preview",
    auth=django_auth,
    response={200: MergePreviewOutput, 400: ErrorResponse, 403: ErrorResponse},
)
def preview_project_merge(request, scope_id: int, target_scope_id: int):
    if not _require_admin(request):
        return Status(403, ADMIN_REQUIRED)
    try:
        return merge_preview(scope_id, target_scope_id)
    except ProjectChangeError as exc:
        return Status(400, {"code": exc.code, "message": exc.message})


@api.post(
    "/review/opportunity-scopes/{scope_id}/merge",
    auth=django_auth,
    response={200: ProjectChangeOutput, 400: ErrorResponse, 403: ErrorResponse},
)
def merge_project(request, scope_id: int, payload: MergeInput):
    """DBGI combines two projects, case by case, with a written reason (decision B3)."""
    if not _require_admin(request):
        return Status(403, ADMIN_REQUIRED)
    try:
        change = merge_projects(
            source_id=scope_id,
            target_id=payload.target_scope_id,
            actor=request.user,
            reason=payload.reason.strip(),
            price_action=payload.price_action,
            order=payload.order,
        )
    except ProjectChangeError as exc:
        return Status(400, {"code": exc.code, "message": exc.message})
    return {"id": change.pk, "decided_at": change.decided_at}


@api.post(
    "/review/registrations/{registration_id}/split",
    auth=django_auth,
    response={201: SplitOutput, 400: ErrorResponse, 403: ErrorResponse, 404: ErrorResponse},
)
def split_registration(request, registration_id: int, payload: SplitInput):
    """DBGI moves some products of a deal to a new deal on another lot (decision B3)."""
    if not _require_admin(request):
        return Status(403, ADMIN_REQUIRED)
    get_object_or_404(Registration, pk=registration_id)
    try:
        new_registration = split_deal(
            registration_id=registration_id,
            item_ids=payload.item_ids,
            target_scope_id=payload.target_scope_id,
            new_lot_name=payload.new_lot_name,
            actor=request.user,
            reason=payload.reason.strip(),
            price_action=payload.price_action,
        )
    except ProjectChangeError as exc:
        return Status(400, {"code": exc.code, "message": exc.message})
    return Status(201, {"id": new_registration.pk, "reference": new_registration.reference})


def _parse_repeat_order_lines(raw_lines):
    """[(item_id, quantity)], or None when the form's lines are not usable."""
    try:
        parsed = json.loads(raw_lines)
        lines = [(int(line["item_id"]), int(line["quantity"])) for line in parsed]
    except (TypeError, ValueError, KeyError):
        return None
    if not lines or any(quantity < 1 for _, quantity in lines):
        return None
    if len({item_id for item_id, _ in lines}) != len(lines):
        return None
    return lines


@api.post(
    "/registrations/{registration_id}/repeat-orders",
    auth=django_auth,
    response={
        201: RepeatOrderOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def request_repeat_order(
    request,
    registration_id: int,
    noa: UploadedFile,
    ntp: UploadedFile,
    lines: Form[str],
    letters_confirmed: Form[bool],
    note: Form[str] = "",
):
    """A partner asks to use the approved price again, with the NOA and NTP (decision D1)."""
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update().select_related("company"),
            pk=registration_id,
            company_id=company_id,
        )
        if registration.status == Registration.Status.WITHDRAWN:
            return Status(409, WITHDRAWN_ERROR)
        choices = {choice["item_id"]: choice for choice in _repeat_order_choices(registration)}
        parsed = _parse_repeat_order_lines(lines)
        if parsed is None or any(item_id not in choices for item_id, _ in parsed):
            return Status(
                400,
                {
                    "code": "invalid_repeat_order",
                    "message": "Choose a quantity for products with a valid approved price.",
                },
            )
        if not letters_confirmed:
            return Status(
                400,
                {
                    "code": "letters_not_confirmed",
                    "message": (
                        "Confirm that both letters are from this end-user and say it is a "
                        "repeat order."
                    ),
                },
            )
        repeat_order = RepeatOrder(
            registration=registration,
            requested_by=request.user,
            noa_file=noa,
            noa_name=noa.name.replace("\\", "/").rsplit("/", 1)[-1],
            ntp_file=ntp,
            ntp_name=ntp.name.replace("\\", "/").rsplit("/", 1)[-1],
            note=note.strip(),
        )
        try:
            repeat_order.full_clean()
        except DjangoValidationError as exc:
            return Status(
                400,
                {
                    "code": "invalid_attachment",
                    "message": "The letters could not be uploaded.",
                    "details": [
                        {"field": field, "message": message}
                        for field, messages in exc.message_dict.items()
                        for message in messages
                    ],
                },
            )
        repeat_order.save()
        RepeatOrderLine.objects.bulk_create(
            [
                RepeatOrderLine(
                    repeat_order=repeat_order,
                    registration_item_id=item_id,
                    quantity=quantity,
                    approved_unit_price=choices[item_id]["approved_unit_price"],
                )
                for item_id, quantity in parsed
            ]
        )
        summary = ", ".join(
            f"{choices[item_id]['product_name']} x {quantity}" for item_id, quantity in parsed
        )
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Repeat order requested",
            details=f"Repeat order requested: {summary}.",
            snapshot=registration_snapshot(registration),
        )
        notify_dbgi_repeat_order_requested(repeat_order)
    return Status(201, _serialize_repeat_order(repeat_order, request.user))


@api.post(
    "/review/repeat-orders/{repeat_order_id}/decision",
    auth=django_auth,
    response={
        200: RepeatOrderOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def decide_repeat_order(request, repeat_order_id: int, payload: RepeatOrderDecisionInput):
    if not _require_admin(request):
        return Status(403, ADMIN_REQUIRED)
    with transaction.atomic():
        repeat_order = get_object_or_404(
            RepeatOrder.objects.select_for_update(of=("self",)).select_related("registration"),
            pk=repeat_order_id,
            status=RepeatOrder.Status.PENDING,
        )
        registration = repeat_order.registration
        if registration.status == Registration.Status.WITHDRAWN:
            return Status(409, WITHDRAWN_ERROR)
        if payload.accept and not all(
            _has_active_price(line.registration_item)
            for line in repeat_order.lines.select_related(
                "registration_item__price_approval__category_approval"
            )
        ):
            return Status(
                400,
                {
                    "code": "price_not_active",
                    "message": "The approved price has ended. It must be renewed before accepting.",
                },
            )
        repeat_order.status = (
            RepeatOrder.Status.ACCEPTED if payload.accept else RepeatOrder.Status.DECLINED
        )
        repeat_order.decision_reason = payload.reason.strip()
        repeat_order.decided_by = request.user
        repeat_order.decided_at = timezone.now()
        repeat_order.save()
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type=f"Repeat order {repeat_order.get_status_display().lower()}",
            details=repeat_order.decision_reason,
            snapshot=registration_snapshot(registration),
        )
        notify_repeat_order_decision(repeat_order)
    return _serialize_repeat_order(repeat_order, request.user)


@api.get(
    "/review/opportunity-scopes",
    auth=django_auth,
    response={200: list[OpportunityScopeOutput], 403: ErrorResponse},
)
def list_opportunity_scopes(request):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    scopes = OpportunityScope.objects.filter(
        is_active=True, opportunity__is_active=True
    ).select_related("opportunity")
    return [
        {
            "id": scope.pk,
            "opportunity_id": scope.opportunity_id,
            "opportunity_title": scope.opportunity.title,
            "name": scope.name,
            "scope_type": scope.scope_type,
            "label": str(scope),
        }
        for scope in scopes
    ]


@api.post(
    "/review/registrations/{registration_id}/suggestion",
    auth=django_auth,
    response={200: MatchingSuggestionOutput, 403: ErrorResponse, 404: ErrorResponse},
)
def refresh_matching_suggestion(request, registration_id: int):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update().prefetch_related("items"),
            pk=registration_id,
        )
        suggestion = generate_matching_suggestion(registration)
    return _serialize_matching_suggestion(suggestion)


WITHDRAWN_ERROR = {
    "code": "registration_withdrawn",
    "message": "This registration was withdrawn and can no longer change.",
}


@api.post(
    "/registrations/{registration_id}/withdraw",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def withdraw_registration(request, registration_id: int, payload: RegistrationWithdrawInput):
    """A partner withdraws its own registration: final, leaves the ranking, and DBGI is notified."""
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A valid company account is required."},
        )
    reason = payload.reason.strip()
    if len(reason) < 5:
        return Status(
            400,
            {
                "code": "validation_error",
                "message": "Correct the highlighted fields.",
                "details": [
                    {
                        "field": "reason",
                        "message": "Explain why you are withdrawing (at least 5 characters).",
                    }
                ],
            },
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(of=("self",)).select_related("company"),
            pk=registration_id,
            company_id=company_id,
        )
        if registration.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": "This registration changed. Refresh before withdrawing.",
                },
            )
        if registration.status not in Registration.WITHDRAWABLE_STATUSES:
            return Status(
                400,
                {
                    "code": "invalid_transition",
                    "message": "This registration can no longer be withdrawn.",
                },
            )
        prior_snapshot = registration_snapshot(registration)
        registration.status = Registration.Status.WITHDRAWN
        registration.needs_review = False
        registration.withdrawn_at = timezone.now()
        registration.version += 1
        registration.save()
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Withdrawn",
            details=reason,
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        notify_dbgi_withdrawal(registration, reason)
    registration = (
        _registration_queryset(request.user)
        .prefetch_related("competitor_items", "items__product", "attachments", "events__actor")
        .select_related("opportunity_scope__opportunity")
        .get(pk=registration_id)
    )
    return _serialize_registration_detail(registration, request.user)


def _detail_response(request, registration_id):
    registration = (
        _registration_queryset(request.user)
        .prefetch_related("competitor_items", "items__product", "attachments", "events__actor")
        .select_related("opportunity_scope__opportunity")
        .get(pk=registration_id)
    )
    return _serialize_registration_detail(registration, request.user)


@api.post(
    "/registrations/{registration_id}/outcome-reports",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def report_project_outcome(request, registration_id: int, payload: OutcomeReportInput):
    """A partner reports its linked project as won, lost, or cancelled; DBGI confirms later."""
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A valid company account is required."},
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(of=("self",)).select_related(
                "company", "opportunity_scope__opportunity"
            ),
            pk=registration_id,
            company_id=company_id,
        )
        blocker = _outcome_report_blocker(registration)
        if blocker:
            return Status(409 if blocker["code"] == "outcome_report_pending" else 400, blocker)
        report = ProjectOutcomeReport.objects.create(
            registration=registration,
            opportunity=registration.opportunity_scope.opportunity,
            outcome=payload.outcome,
            note=payload.note.strip(),
            reported_by=request.user,
        )
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Outcome reported",
            details=f"Reported the project as {report.get_outcome_display()}: {report.note}",
            snapshot=registration_snapshot(registration),
        )
        notify_outcome_reported(report)
    return _detail_response(request, registration_id)


@api.post(
    "/review/registration-items/{item_id}/catalog",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def add_item_to_catalog(request, item_id: int, payload: CatalogLinkInput):
    """Decision C4: DBGI puts a typed-in product in the catalog, which opens its price review."""
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    if bool(payload.product_id) == bool(payload.new_product):
        return Status(
            400,
            {
                "code": "validation_error",
                "message": "Choose an existing product or describe a new one.",
            },
        )
    with transaction.atomic():
        item = get_object_or_404(
            RegistrationItem.objects.select_related("registration"), pk=item_id
        )
        registration = Registration.objects.select_for_update().get(pk=item.registration_id)
        if registration.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": "This registration changed. Refresh before updating the catalog.",
                },
            )
        if item.product_id or registration.status in {
            Registration.Status.WITHDRAWN,
            Registration.Status.REJECTED,
        }:
            return Status(
                400,
                {
                    "code": "invalid_transition",
                    "message": "This line cannot be added to the catalog.",
                },
            )
        reason = payload.reason.strip()
        if payload.new_product:
            new = payload.new_product
            if Product.objects.filter(code__iexact=new.code.strip()).exists():
                return Status(
                    409,
                    {
                        "code": "duplicate_product",
                        "message": "A product with this code already exists. Link it instead.",
                    },
                )
            category = new.category.strip()
        else:
            existing = get_object_or_404(Product, pk=payload.product_id, is_active=True)
            category = existing.category
        decided = (
            registration.category_approvals.filter(category=category)
            .exclude(
                status__in=[
                    RegistrationCategoryApproval.Status.PENDING,
                    RegistrationCategoryApproval.Status.CHANGES_REQUESTED,
                ]
            )
            .exists()
        )
        if decided:
            return Status(
                409,
                {
                    "code": "commercial_review_locked",
                    "message": (
                        "This category's prices were already decided. "
                        "Request changes on them first."
                    ),
                },
            )
        if payload.new_product:
            created = Product.objects.create(
                code=new.code.strip(), name=new.name.strip(), category=category
            )
            ProductPrice.objects.create(
                product=created, unit_price=new.list_price, reason=reason, created_by=request.user
            )
            product_id = created.pk
        else:
            product_id = existing.pk
        product = Product.objects.with_list_price().get(pk=product_id)
        prior_snapshot = registration_snapshot(registration)
        typed_name = item.non_catalog_name
        item.product = product
        item.non_catalog_name = ""
        _capture_price(item, product, RegistrationItem.PriceBasis.ORIGINAL)
        item.save()
        RegistrationCategoryApproval.objects.get_or_create(
            registration=registration, category=category
        )
        registration.version += 1
        registration.save(update_fields=["version", "updated_at"])
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Product added to catalog",
            details=f"{typed_name} is now {product}. {reason}",
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        notify_company_users(
            registration=registration,
            event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
            event_key=f"catalog-item:{item.pk}",
            title="Product added to the catalog",
            message=(
                f"DBGI added a product you requested on {registration.reference} to the catalog. "
                "Its price can now be reviewed."
            ),
        )
    return _detail_response(request, registration.pk)


@api.post(
    "/review/registrations/{registration_id}/reprice",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def reprice_registration(request, registration_id: int, payload: RegistrationRepriceInput):
    """DBGI explicitly applies the current list prices to a registration, with a reason."""
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(of=("self",)), pk=registration_id
        )
        if registration.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": "This registration changed. Refresh before repricing.",
                },
            )
        if registration.status in {Registration.Status.WITHDRAWN, Registration.Status.REJECTED}:
            return Status(
                400,
                {
                    "code": "invalid_transition",
                    "message": "A withdrawn or rejected registration cannot be repriced.",
                },
            )
        if _commercial_review_started(registration):
            return Status(
                409,
                {
                    "code": "commercial_review_locked",
                    "message": "Prices cannot be recaptured after commercial review has started.",
                },
            )
        prior_snapshot = registration_snapshot(registration)
        items = list(registration.items.filter(product__isnull=False))
        products = {
            product.pk: product
            for product in Product.objects.with_list_price().filter(
                pk__in=[item.product_id for item in items]
            )
        }
        for item in items:
            _capture_price(
                item, products[item.product_id], RegistrationItem.PriceBasis.DBGI_DECISION
            )
            item.save()
        registration.version += 1
        registration.save(update_fields=["version", "updated_at"])
        reason = payload.reason.strip()
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="List prices updated by DBGI",
            details=reason,
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        notify_company_users(
            registration=registration,
            event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
            event_key=f"reprice:{registration.pk}:v{registration.version}",
            title="List prices updated by DBGI",
            message=(
                f"DBGI applied the current list prices to {registration.reference}. "
                "Open the registration to read the reason."
            ),
        )
    return _detail_response(request, registration_id)


@api.post(
    "/review/outcome-reports/{report_id}/decision",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
    },
)
def decide_outcome_report(request, report_id: int, payload: OutcomeDecisionInput):
    """DBGI confirms a reported outcome (setting the project status) or declines it."""
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    note = payload.note.strip()
    with transaction.atomic():
        report = get_object_or_404(
            ProjectOutcomeReport.objects.select_for_update(of=("self",)).select_related(
                "registration__company", "opportunity"
            ),
            pk=report_id,
        )
        if report.status != ProjectOutcomeReport.Status.PENDING:
            return Status(
                400,
                {"code": "invalid_transition", "message": "This report was already decided."},
            )
        report.status = (
            ProjectOutcomeReport.Status.CONFIRMED
            if payload.confirm
            else ProjectOutcomeReport.Status.REJECTED
        )
        report.decided_by = request.user
        report.decided_at = timezone.now()
        report.decision_note = note
        report.save()
        if payload.confirm:
            opportunity = Opportunity.objects.select_for_update().get(pk=report.opportunity_id)
            _set_project_status(
                opportunity, report.outcome, request.user, f"Confirmed the reported outcome. {note}"
            )
        else:
            RegistrationEvent.objects.create(
                registration=report.registration,
                actor=request.user,
                event_type="Outcome report not accepted",
                details=note,
                snapshot=registration_snapshot(report.registration),
            )
        notify_outcome_decision(report)
    return _detail_response(request, report.registration_id)


@api.post(
    "/review/registrations/{registration_id}/decision",
    auth=django_auth,
    response={
        200: RegistrationDetail,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def review_registration(request, registration_id: int, payload: ReviewDecisionInput):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    transitions = {
        RegistrationReviewDecision.Decision.START_REVIEW: {
            Registration.Status.SUBMITTED,
            Registration.Status.RESUBMITTED,
            Registration.Status.REVIEW_REQUIRED,
        },
        RegistrationReviewDecision.Decision.REQUEST_CHANGES: {Registration.Status.UNDER_REVIEW},
        RegistrationReviewDecision.Decision.CONFIRM_MATCH: {Registration.Status.UNDER_REVIEW},
        RegistrationReviewDecision.Decision.REJECT: {Registration.Status.UNDER_REVIEW},
    }
    target_status = {
        RegistrationReviewDecision.Decision.START_REVIEW: Registration.Status.UNDER_REVIEW,
        RegistrationReviewDecision.Decision.REQUEST_CHANGES: Registration.Status.CHANGES_REQUESTED,
        RegistrationReviewDecision.Decision.CONFIRM_MATCH: Registration.Status.ELIGIBLE_MATCHED,
        RegistrationReviewDecision.Decision.REJECT: Registration.Status.REJECTED,
    }[payload.decision]
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(of=("self",)).select_related(
                "company", "opportunity_scope"
            ),
            pk=registration_id,
        )
        if registration.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": "This registration changed. Refresh before deciding.",
                },
            )
        if registration.status not in transitions[payload.decision]:
            return Status(
                400,
                {
                    "code": "invalid_transition",
                    "message": "That review action is not available from the current status.",
                },
            )

        scope = None
        if payload.decision == RegistrationReviewDecision.Decision.CONFIRM_MATCH:
            if payload.create_new_opportunity:
                opportunity = Opportunity.objects.create(
                    title=registration.project_title,
                    end_user=registration.end_user,
                    end_user_name=registration.end_user_name,
                    end_user_address=registration.end_user_address,
                    created_by=request.user,
                )
                scope = OpportunityScope.objects.create(
                    opportunity=opportunity,
                    name="Whole opportunity",
                    scope_type=OpportunityScope.ScopeType.WHOLE,
                )
            elif payload.opportunity_scope_id:
                scope = get_object_or_404(
                    OpportunityScope,
                    pk=payload.opportunity_scope_id,
                    is_active=True,
                    opportunity__is_active=True,
                )
            else:
                return Status(
                    400,
                    {
                        "code": "scope_required",
                        "message": "Choose an opportunity scope or create a new opportunity.",
                    },
                )

        prior_snapshot = registration_snapshot(registration)
        suggestion = registration.matching_suggestions.filter(is_current=True).first()
        registration.status = target_status
        registration.needs_review = target_status in {
            Registration.Status.CHANGES_REQUESTED,
            Registration.Status.REVIEW_REQUIRED,
        }
        if scope:
            registration.opportunity_scope = scope
        registration.version += 1
        registration.save()
        decision = RegistrationReviewDecision.objects.create(
            registration=registration,
            suggestion=suggestion,
            opportunity_scope=scope,
            decision=payload.decision,
            rationale=payload.rationale.strip(),
            actor=request.user,
            registration_version=registration.version,
        )
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type=decision.get_decision_display(),
            details=decision.rationale,
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
        notify_registration_decision(registration, decision)
    registration = (
        _registration_queryset(request.user)
        .prefetch_related("competitor_items", "items__product", "attachments", "events__actor")
        .select_related("opportunity_scope__opportunity")
        .get(pk=registration_id)
    )
    return _serialize_registration_detail(registration, request.user)


@api.post(
    "/review/category-approvals/{approval_id}/decision",
    auth=django_auth,
    response={
        200: CategoryApprovalOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def decide_category_approval(request, approval_id: int, payload: CategoryApprovalDecisionInput):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        approval = get_object_or_404(
            RegistrationCategoryApproval.objects.select_for_update(of=("self",)).select_related(
                "registration", "reviewed_by"
            ),
            pk=approval_id,
        )
        if approval.version != payload.version:
            return Status(
                409,
                {
                    "code": "edit_conflict",
                    "message": "This commercial approval changed. Refresh before deciding.",
                },
            )
        if approval.registration.status == Registration.Status.WITHDRAWN:
            return Status(409, WITHDRAWN_ERROR)
        items = list(
            approval.registration.items.select_related("product").filter(
                product__category=approval.category
            )
        )
        item_ids = {item.pk for item in items}
        unexpected_ids = set(payload.approved_prices) - item_ids
        if unexpected_ids:
            return Status(
                400,
                {
                    "code": "invalid_approved_item",
                    "message": "An approved price refers to an item outside this category.",
                },
            )
        if payload.status in {
            RegistrationCategoryApproval.Status.APPROVED,
            RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
        }:
            if not payload.valid_until:
                # Decision C1: approved prices are valid for 90 days unless DBGI sets a date
                payload.valid_until = timezone.localdate() + timedelta(days=90)
            if payload.valid_until < timezone.localdate():
                return Status(
                    400,
                    {
                        "code": "valid_until_required",
                        "message": (
                            "Approved commercial terms require a current or future expiry date."
                        ),
                    },
                )
            required_count = (
                len(items) if payload.status == RegistrationCategoryApproval.Status.APPROVED else 1
            )
            if len(payload.approved_prices) < required_count:
                return Status(
                    400,
                    {
                        "code": "approved_prices_required",
                        "message": (
                            "Enter approved prices for the products covered by this decision."
                        ),
                    },
                )
        prior_snapshot = registration_snapshot(approval.registration)
        approval.status = payload.status
        approval.rationale = payload.rationale.strip()
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()
        approval.valid_until = payload.valid_until
        approval.expiry_reminder_sent_at = None
        approval.version += 1
        approval.save()
        approval.item_approvals.all().delete()
        RegistrationItemApproval.objects.bulk_create(
            [
                RegistrationItemApproval(
                    category_approval=approval,
                    registration_item=item,
                    approved_unit_price=payload.approved_prices.get(item.pk),
                )
                for item in items
                if item.pk in payload.approved_prices
            ]
        )
        approval.registration.version += 1
        approval.registration.save(update_fields=["version", "updated_at"])
        RegistrationEvent.objects.create(
            registration=approval.registration,
            actor=request.user,
            event_type="Commercial decision",
            details=(
                f"{approval.category} pricing was marked {approval.get_status_display()}. "
                f"{approval.rationale}"
            ),
            snapshot=prior_snapshot,
        )
        notify_price_decision(approval)
    return _serialize_category_approval(approval)


@api.post(
    "/review/opportunities/{opportunity_id}/project-status",
    auth=django_auth,
    response={200: OpportunityScopeOutput, 403: ErrorResponse, 404: ErrorResponse},
)
def update_project_status(request, opportunity_id: int, payload: ProjectStatusInput):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        opportunity = get_object_or_404(
            Opportunity.objects.select_for_update(), pk=opportunity_id, is_active=True
        )
        _set_project_status(opportunity, payload.status, request.user, payload.reason.strip())
    scope = opportunity.scopes.filter(is_active=True).first()
    if not scope:
        return Status(
            404,
            {"code": "scope_not_found", "message": "The opportunity has no active scope."},
        )
    return {
        "id": scope.pk,
        "opportunity_id": opportunity.pk,
        "opportunity_title": opportunity.title,
        "name": scope.name,
        "scope_type": scope.scope_type,
        "label": str(scope),
    }


@api.post(
    "/category-approvals/{approval_id}/renewals",
    auth=django_auth,
    response={
        201: CategoryApprovalOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def request_price_renewal(request, approval_id: int, payload: RenewalRequestInput):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403, {"code": "company_access_required", "message": "A company account is required."}
        )
    approval = get_object_or_404(
        RegistrationCategoryApproval.objects.select_related("registration", "reviewed_by"),
        pk=approval_id,
        registration__company_id=company_id,
    )
    if approval.status not in {
        RegistrationCategoryApproval.Status.APPROVED,
        RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
    }:
        return Status(
            400,
            {
                "code": "renewal_unavailable",
                "message": "Only approved commercial terms can be renewed.",
            },
        )
    if approval.registration.status == Registration.Status.WITHDRAWN:
        return Status(409, WITHDRAWN_ERROR)
    if approval.renewals.filter(status=PriceApprovalRenewal.Status.PENDING).exists():
        return Status(
            400,
            {"code": "renewal_pending", "message": "A renewal request is already pending."},
        )
    renewal = PriceApprovalRenewal.objects.create(
        category_approval=approval,
        requested_by=request.user,
        reason=payload.reason.strip(),
        previous_valid_until=approval.valid_until,
    )
    RegistrationEvent.objects.create(
        registration=approval.registration,
        actor=request.user,
        event_type="Price renewal requested",
        details=f"Renewal requested for {approval.category}: {payload.reason.strip()}",
        snapshot=registration_snapshot(approval.registration),
    )
    notify_dbgi_renewal_requested(approval, renewal)
    return Status(201, _serialize_category_approval(approval))


@api.post(
    "/review/renewals/{renewal_id}/decision",
    auth=django_auth,
    response={
        200: CategoryApprovalOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def decide_price_renewal(request, renewal_id: int, payload: RenewalDecisionInput):
    if not _require_admin(request):
        return Status(
            403, {"code": "admin_required", "message": "DBGI administrator access is required."}
        )
    with transaction.atomic():
        renewal = get_object_or_404(
            PriceApprovalRenewal.objects.select_for_update(of=("self",)).select_related(
                "category_approval__registration", "category_approval__reviewed_by"
            ),
            pk=renewal_id,
            status=PriceApprovalRenewal.Status.PENDING,
        )
        approval = renewal.category_approval
        if approval.registration.status == Registration.Status.WITHDRAWN:
            return Status(409, WITHDRAWN_ERROR)
        renewal.decided_by = request.user
        renewal.decided_at = timezone.now()
        renewal.decision_reason = payload.reason.strip()
        if payload.approve:
            today = timezone.localdate()
            base_date = (
                approval.valid_until
                if approval.valid_until and approval.valid_until >= today
                else today
            )
            renewal.status = PriceApprovalRenewal.Status.APPROVED
            renewal.new_valid_until = base_date + timedelta(days=30)
            approval.valid_until = renewal.new_valid_until
            approval.expiry_reminder_sent_at = None
            approval.version += 1
            approval.save(
                update_fields=["valid_until", "expiry_reminder_sent_at", "version", "updated_at"]
            )
        else:
            renewal.status = PriceApprovalRenewal.Status.REJECTED
        renewal.save()
        approval.registration.version += 1
        approval.registration.save(update_fields=["version", "updated_at"])
        RegistrationEvent.objects.create(
            registration=approval.registration,
            actor=request.user,
            event_type="Price renewal decided",
            details=(
                f"The {approval.category} renewal was "
                f"{'approved' if payload.approve else 'rejected'}: {payload.reason.strip()}"
            ),
            snapshot=registration_snapshot(approval.registration),
        )
        notify_company_users(
            registration=approval.registration,
            event_type=RegistrationNotification.EventType.PRICE_DECISION,
            event_key=f"renewal:{renewal.pk}:decided",
            title="Price renewal approved" if payload.approve else "Price renewal declined",
            message=(
                f"DBGI decided your {approval.category} price renewal for "
                f"{approval.registration.reference}. Open the registration to read the reason."
            ),
        )
    return _serialize_category_approval(approval)


def _attachment_edit_guard(registration, version):
    if registration.status in Registration.EVIDENCE_LOCKED_STATUSES:
        return Status(
            409,
            {
                "code": "evidence_locked",
                "message": (
                    "Attachments cannot change once review has started or a decision exists."
                ),
            },
        )
    if registration.version != version:
        return Status(
            409,
            {
                "code": "edit_conflict",
                "message": (
                    "This registration changed after you opened it. Refresh before changing "
                    "the attachments."
                ),
            },
        )
    return None


@api.post(
    "/registrations/{registration_id}/finalize",
    auth=django_auth,
    response={
        200: RegistrationListItem,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def finalize_registration(request, registration_id: int, payload: RegistrationFinalize):
    """Commit a saved registration once its evidence transfers have finished.

    The company form saves fields first and moves files afterwards, so the
    version it holds is only final after this call. Bumping it here keeps a
    half-finished submit from looking complete to another editor.
    """
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(),
            pk=registration_id,
            company_id=company_id,
        )
        guard = _attachment_edit_guard(registration, payload.version)
        if guard:
            return guard
        prior_snapshot = registration_snapshot(registration)
        registration.version += 1
        registration.save(update_fields=["version", "updated_at"])
        if _alerts_dbgi_on_attachment_change(registration):
            notify_dbgi_review_needed(registration, "attachment files changed")
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Attachments submitted",
            details=(
                "Company finished submitting the registration and its attachments. "
                f"Version is now {registration.version}."
            ),
            snapshot=prior_snapshot,
        )
    return _serialize_registration(registration)


@api.post(
    "/registrations/{registration_id}/attachments",
    auth=django_auth,
    response={
        201: AttachmentOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def upload_attachment(
    request,
    registration_id: int,
    file: UploadedFile,
    version: int,
    description: str = "",
):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    with transaction.atomic():
        registration = get_object_or_404(
            Registration.objects.select_for_update(),
            pk=registration_id,
            company_id=company_id,
        )
        guard = _attachment_edit_guard(registration, version)
        if guard:
            return guard
        attachment = registration.attachments.model(
            registration=registration,
            file=file,
            original_name=file.name.replace("\\", "/").rsplit("/", 1)[-1],
            description=description,
            uploaded_by=request.user,
        )
        try:
            attachment.full_clean()
        except DjangoValidationError as exc:
            return Status(
                400,
                {
                    "code": "invalid_attachment",
                    "message": "The attachment could not be uploaded.",
                    "details": [
                        {"field": field, "message": message}
                        for field, messages in exc.message_dict.items()
                        for message in messages
                    ],
                },
            )
        prior_snapshot = registration_snapshot(registration)
        attachment.save()
        _flag_attachment_change(registration)
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Attachment added",
            details=f"{attachment.original_name} was added to the attachments."
            + (f" Description: {description}" if description else ""),
            snapshot=prior_snapshot,
        )
    return Status(
        201,
        {
            "id": attachment.pk,
            "original_name": attachment.original_name,
            "description": attachment.description,
            "uploaded_at": attachment.uploaded_at,
            "download_url": f"/attachments/{attachment.pk}/download/",
        },
    )


@api.delete(
    "/attachments/{attachment_id}",
    auth=django_auth,
    response={
        204: None,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        409: ErrorResponse,
    },
)
def delete_attachment(request, attachment_id: int, version: int):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    with transaction.atomic():
        attachment = get_object_or_404(
            RegistrationAttachment.objects.select_related("registration"),
            pk=attachment_id,
            registration__company_id=company_id,
        )
        registration = Registration.objects.select_for_update().get(pk=attachment.registration_id)
        guard = _attachment_edit_guard(registration, version)
        if guard:
            return guard
        original_name = attachment.original_name
        prior_snapshot = registration_snapshot(registration)
        attachment.delete()
        _flag_attachment_change(registration)
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Attachment removed",
            details=f"{original_name} was removed from the attachments.",
            snapshot=prior_snapshot,
        )
    return Status(204, None)
