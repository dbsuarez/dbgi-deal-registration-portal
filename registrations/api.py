from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from ninja import Field, NinjaAPI, Schema, Status, UploadedFile
from ninja.errors import AuthenticationError
from ninja.errors import ValidationError as NinjaValidationError
from ninja.security import django_auth

from .audit import registration_snapshot
from .models import (
    CompetitorItem,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationEvent,
    RegistrationItem,
)

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
    end_user_name: str
    end_user_address: str
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


class RegistrationUpdate(RegistrationInput):
    version: int


class RegistrationListItem(Schema):
    id: int
    reference: str
    project_title: str
    company_name: str
    end_user_name: str
    status: str
    status_label: str
    needs_review: bool
    created_at: datetime
    version: int


class RegistrationListResponse(Schema):
    items: list[RegistrationListItem]
    total: int
    page: int
    page_size: int


class CompetitorOutput(CompetitorInput):
    id: int


class RegistrationItemOutput(RegistrationItemInput):
    id: int
    product_code: str | None
    product_name: str | None
    display_name: str


class AttachmentOutput(Schema):
    id: int
    original_name: str
    description: str
    uploaded_at: datetime
    download_url: str


class EventOutput(Schema):
    id: int
    event_type: str
    details: str
    actor_name: str
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


class ProductOption(Schema):
    id: int
    code: str
    name: str
    category: str


class SessionResponse(Schema):
    username: str
    display_name: str
    is_dbgi_admin: bool
    csrf_token: str


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
        "is_dbgi_admin": request.user.is_dbgi_admin,
        "csrf_token": get_token(request),
    }


@api.post("/session/logout", auth=django_auth, response={204: None})
def logout_session(request):
    django_logout(request)
    return Status(204, None)


def _company_id(user):
    if user.is_dbgi_admin:
        return None
    if user.role != user.Role.COMPANY or not user.company_id or not user.company.is_active:
        return False
    return user.company_id


def _registration_queryset(user):
    company_id = _company_id(user)
    queryset = Registration.objects.select_related("company", "submitted_by")
    if company_id is False:
        return queryset.none()
    if company_id is not None:
        queryset = queryset.filter(company_id=company_id)
    return queryset


def _serialize_registration(registration):
    return {
        "id": registration.pk,
        "reference": registration.reference,
        "project_title": registration.project_title,
        "company_name": registration.company.name,
        "end_user_name": registration.end_user_name,
        "status": registration.status,
        "status_label": registration.get_status_display(),
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
                }
                for event in registration.events.select_related("actor").all()
            ],
        }
    )
    return detail


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
    total = queryset.count()
    start = (page - 1) * page_size
    records = queryset.order_by(sort)[start : start + page_size]
    return {
        "items": [_serialize_registration(record) for record in records],
        "total": total,
        "page": page,
        "page_size": page_size,
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
    registration.competitor_items.all().delete()
    registration.items.all().delete()
    CompetitorItem.objects.bulk_create(
        [
            CompetitorItem(registration=registration, **item.model_dump())
            for item in payload.competitor_items
        ]
    )
    product_ids = {item.product_id for item in payload.items if item.product_id}
    products = {
        product.pk: product
        for product in Product.objects.filter(pk__in=product_ids, is_active=True)
    }
    if len(products) != len(product_ids):
        return False
    RegistrationItem.objects.bulk_create(
        [
            RegistrationItem(
                registration=registration,
                product=products.get(item.product_id),
                non_catalog_name=item.non_catalog_name,
                quantity=item.quantity,
                requested_unit_price=item.requested_unit_price,
                justification=item.justification,
            )
            for item in payload.items
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
    values = payload.model_dump(exclude={"competitor_items", "items"})
    with transaction.atomic():
        registration = Registration.objects.create(
            company_id=company_id,
            submitted_by=request.user,
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
        prior_snapshot = registration_snapshot(registration)
        for name, value in payload.model_dump(
            exclude={"competitor_items", "items", "version"}
        ).items():
            setattr(registration, name, value)
        registration.version += 1
        registration.needs_review = True
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
        )
    return _serialize_registration(registration)


@api.post(
    "/registrations/{registration_id}/attachments",
    auth=django_auth,
    response={201: AttachmentOutput, 400: ErrorResponse, 403: ErrorResponse},
)
def upload_attachment(
    request,
    registration_id: int,
    file: UploadedFile,
    description: str = "",
):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    registration = get_object_or_404(
        Registration,
        pk=registration_id,
        company_id=company_id,
    )
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
    attachment.save()
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
    response={204: None, 403: ErrorResponse},
)
def delete_attachment(request, attachment_id: int):
    company_id = _company_id(request.user)
    if company_id in (None, False):
        return Status(
            403,
            {"code": "company_access_required", "message": "A company account is required."},
        )
    attachment = get_object_or_404(
        RegistrationAttachment.objects.select_related("registration"),
        pk=attachment_id,
        registration__company_id=company_id,
    )
    attachment.delete()
    return Status(204, None)
