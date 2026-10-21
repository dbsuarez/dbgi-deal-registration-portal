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
from ninja import Field, NinjaAPI, Schema, Status, UploadedFile
from ninja.errors import AuthenticationError
from ninja.errors import ValidationError as NinjaValidationError
from ninja.security import django_auth

from .audit import registration_change_details, registration_snapshot
from .matching import generate_matching_suggestion
from .models import (
    CompetitorBrand,
    CompetitorBrandAlias,
    CompetitorItem,
    CompetitorModel,
    EndUser,
    Opportunity,
    OpportunityScope,
    PriceApprovalRenewal,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationItemApproval,
    RegistrationNotification,
    RegistrationReviewDecision,
)
from .notifications import notify_price_decision, notify_registration_decision, notify_submission

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
    updated_at: datetime


class RegistrationUpdate(RegistrationInput):
    version: int


class RegistrationFinalize(Schema):
    version: int
    evidence_changed: bool = False


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


class RegistrationDetail(RegistrationListItem):
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
    csrf_token: str


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


class RankingEntryOutput(Schema):
    rank: int
    is_tied: bool
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
    return {
        "username": request.user.username,
        "display_name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "designation": request.user.designation,
        "phone_number": request.user.phone_number,
        "is_dbgi_admin": request.user.is_dbgi_admin,
        "is_debug": settings.DEBUG,
        "csrf_token": get_token(request),
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

    return RegistrationTestPreset.objects.filter(owner=request.user)


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

    preset = get_object_or_404(RegistrationTestPreset, pk=preset_id, owner=request.user)
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
                "message": "You already have test data with this name.",
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

    preset = get_object_or_404(RegistrationTestPreset, pk=preset_id, owner=request.user)
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


def _serialize_registration_detail(registration, user):
    detail = _serialize_registration(registration)
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
            "can_edit": not user.is_dbgi_admin,
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
            "events": [
                {
                    "id": event.pk,
                    "event_type": event.event_type,
                    "details": event.details,
                    "actor_name": (
                        (event.actor.get_full_name() or event.actor.username)
                        if event.actor_id
                        else "System"
                    ),
                    "created_at": event.created_at,
                    "changes": registration_change_details(
                        event.snapshot, event.resulting_snapshot
                    ),
                }
                for event in registration.events.select_related("actor").all()
            ],
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
                {
                    "id": approval.pk,
                    "category": approval.category,
                    "status": approval.effective_status,
                    "status_label": RegistrationCategoryApproval.Status(
                        approval.effective_status
                    ).label,
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
                for approval in registration.category_approvals.select_related("reviewed_by").all()
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
    return {
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
    queryset = Product.objects.filter(is_active=True)
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
                "message": "Confirm authorization to share the evidence.",
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


def _save_children(registration, payload):
    registration.category_approvals.filter(
        status=RegistrationCategoryApproval.Status.PENDING
    ).delete()
    registration.competitor_items.all().delete()
    registration.items.all().delete()
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
        for product in Product.objects.filter(pk__in=product_ids, is_active=True)
    }
    if len(products) != len(product_ids):
        return False
    saved_items = RegistrationItem.objects.bulk_create(
        [
            RegistrationItem(
                registration=registration,
                product=products.get(item.product_id),
                non_catalog_name=item.non_catalog_name,
                quantity=item.quantity,
                requested_unit_price=item.requested_unit_price,
                currency=(products[item.product_id].currency if item.product_id else "PHP"),
                list_unit_price_snapshot=(
                    products[item.product_id].list_price if item.product_id else Decimal("0.00")
                ),
                justification=item.justification,
            )
            for item in payload.items
        ]
    )
    categories = sorted(
        {item.product.category for item in saved_items if item.product_id and item.product}
    )
    RegistrationCategoryApproval.objects.bulk_create(
        [
            RegistrationCategoryApproval(registration=registration, category=category)
            for category in categories
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
        if registration.category_approvals.exclude(
            status=RegistrationCategoryApproval.Status.PENDING
        ).exists():
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
        for name, value in payload.model_dump(
            exclude={"competitor_items", "items", "version", "end_user_id"}
        ).items():
            setattr(registration, name, value)
        registration.end_user = end_user
        registration.end_user_name = end_user.official_name
        registration.end_user_address = end_user.full_address
        registration.version += 1
        registration.needs_review = True
        if registration.status == Registration.Status.CHANGES_REQUESTED:
            registration.status = Registration.Status.RESUBMITTED
        elif registration.status == Registration.Status.ELIGIBLE_MATCHED:
            registration.status = Registration.Status.REVIEW_REQUIRED
        registration.save()
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
            event_type="Company edit",
            details="Company updated the registration; DBGI review is required.",
            snapshot=prior_snapshot,
            resulting_snapshot=registration_snapshot(registration),
        )
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

    registrations = (
        Registration.objects.filter(
            status=Registration.Status.ELIGIBLE_MATCHED,
            opportunity_scope_id__in=scope_ids,
        )
        .select_related("company")
        .order_by("opportunity_scope_id", "original_submitted_at", "id")
    )
    registrations_by_scope = defaultdict(list)
    seen_companies = set()
    for registration in registrations:
        company_key = (registration.opportunity_scope_id, registration.company_id)
        if company_key in seen_companies:
            continue
        seen_companies.add(company_key)
        registrations_by_scope[registration.opportunity_scope_id].append(registration)

    items = []
    for scope in page_scopes:
        ranked = registrations_by_scope[scope.pk]
        timestamp_counts = Counter(item.original_submitted_at for item in ranked)
        entries = []
        current_rank = 0
        prior_timestamp = None
        for position, registration in enumerate(ranked, start=1):
            if registration.original_submitted_at != prior_timestamp:
                current_rank = position
                prior_timestamp = registration.original_submitted_at
            if company_id is None or registration.company_id == company_id:
                entries.append(
                    {
                        "rank": current_rank,
                        "is_tied": timestamp_counts[registration.original_submitted_at] > 1,
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
            if not payload.valid_until or payload.valid_until < timezone.localdate():
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
        old_label = opportunity.get_project_status_display()
        opportunity.project_status = payload.status
        opportunity.save(update_fields=["project_status"])
        registrations = Registration.objects.filter(opportunity_scope__opportunity=opportunity)
        for registration in registrations:
            RegistrationEvent.objects.create(
                registration=registration,
                actor=request.user,
                event_type="Project status changed",
                details=(
                    f"Project status changed from {old_label} to "
                    f"{opportunity.get_project_status_display()}: {payload.reason.strip()}"
                ),
                snapshot=registration_snapshot(registration),
            )
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
    if approval.renewals.filter(status=PriceApprovalRenewal.Status.PENDING).exists():
        return Status(
            400,
            {"code": "renewal_pending", "message": "A renewal request is already pending."},
        )
    PriceApprovalRenewal.objects.create(
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
    return Status(201, _serialize_category_approval(approval))


@api.post(
    "/review/renewals/{renewal_id}/decision",
    auth=django_auth,
    response={
        200: CategoryApprovalOutput,
        400: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
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
            approval.version += 1
            approval.save(update_fields=["valid_until", "version", "updated_at"])
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
    return _serialize_category_approval(approval)


def _attachment_edit_guard(registration, version):
    if registration.status in Registration.EVIDENCE_LOCKED_STATUSES:
        return Status(
            409,
            {
                "code": "evidence_locked",
                "message": ("Evidence cannot change once review has started or a decision exists."),
            },
        )
    if registration.version != version:
        return Status(
            409,
            {
                "code": "edit_conflict",
                "message": (
                    "This registration changed after you opened it. Refresh before changing "
                    "the evidence."
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
        if payload.evidence_changed:
            registration.needs_review = True
        registration.save(update_fields=["version", "needs_review", "updated_at"])
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Evidence submitted",
            details=(
                "Company finished submitting the registration and its evidence set. "
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
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Attachment added",
            details=f"{attachment.original_name} was added to the evidence set."
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
        RegistrationEvent.objects.create(
            registration=registration,
            actor=request.user,
            event_type="Attachment removed",
            details=f"{original_name} was removed from the evidence set.",
            snapshot=prior_snapshot,
        )
    return Status(204, None)
