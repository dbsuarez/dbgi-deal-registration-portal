from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from registrations.audit import registration_snapshot
from registrations.matching import generate_matching_suggestion
from registrations.models import (
    Company,
    CompetitorItem,
    EndUser,
    Opportunity,
    OpportunityScope,
    Product,
    Registration,
    RegistrationEvent,
    RegistrationItem,
    RegistrationReviewDecision,
    User,
)


@dataclass(frozen=True)
class ScenarioDefinition:
    key: str
    title: str
    summary: str
    expected_result: str


SCENARIOS = {
    "automatic_exact": ScenarioDefinition(
        key="automatic_exact",
        title="Automatic exact match",
        summary=(
            "IT Avenue submits first and Lexmark later submits the same normalized End-user, "
            "address, and complete product set."
        ),
        expected_result=(
            "Lexmark is automatically linked to the same printer lot at 100% confidence. "
            "IT Avenue ranks first and Lexmark ranks second without administrator review."
        ),
    ),
    "ambiguous_match": ScenarioDefinition(
        key="ambiguous_match",
        title="Ambiguous exact match",
        summary=(
            "Two active scopes have the same normalized End-user, address, and product evidence "
            "before Lexmark submits."
        ),
        expected_result=(
            "Lexmark remains submitted. The matcher requests clarification because choosing one "
            "of two exact scopes automatically would be unsafe."
        ),
    ),
    "material_edit": ScenarioDefinition(
        key="material_edit",
        title="Material edit after matching",
        summary=(
            "Lexmark is matched automatically, then changes the delivery location to a materially "
            "different address."
        ),
        expected_result=(
            "The prior scope stays visible for context, but the registration changes to Review "
            "required after edit and the new suggestion records an address conflict."
        ),
    ),
}


def _company_user(company_name, email):
    company, _ = Company.objects.get_or_create(name=company_name)
    company.is_active = True
    company.save(update_fields=["is_active"])
    user, _ = User.objects.get_or_create(username=email)
    user.email = email
    user.role = User.Role.COMPANY
    user.company = company
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.set_password("testpass123")
    user.save()
    return user


def _product(code):
    defaults = {
        "M1820W": ("20 ppm monochrome laser printer", "Laser Printers"),
        "P1820W": ("20 ppm monochrome multifunction printer", "Laser Printers"),
    }
    name, category = defaults[code]
    product, _ = Product.objects.get_or_create(
        code=code,
        defaults={"name": name, "category": category},
    )
    return product


def _opportunity(actor, *, title, end_user_name, address, scope_name):
    end_user, _ = EndUser.objects.update_or_create(
        normalized_name=" ".join(end_user_name.lower().split()),
        normalized_address=" ".join(address.lower().split()),
        defaults={
            "official_name": end_user_name,
            "city_municipality": "Development scenario",
            "street_address": address,
            "status": EndUser.Status.VERIFIED,
            "is_active": True,
            "created_by": actor,
            "verified_by": actor,
            "verified_at": timezone.now(),
        },
    )
    opportunity, _ = Opportunity.objects.update_or_create(
        title=title,
        defaults={
            "end_user_name": end_user_name,
            "end_user_address": address,
            "end_user": end_user,
            "is_active": True,
            "created_by": actor,
        },
    )
    scope, _ = OpportunityScope.objects.update_or_create(
        opportunity=opportunity,
        name=scope_name,
        defaults={
            "scope_type": OpportunityScope.ScopeType.LOT,
            "description": "Development scenario ranking scope.",
            "is_active": True,
        },
    )
    return scope


def _registration(
    *,
    company_user,
    title,
    end_user_name,
    address,
    product,
    submitted_at,
    end_user,
):
    registration = Registration.objects.filter(
        company=company_user.company,
        project_title=title,
    ).first()
    if registration is None:
        registration = Registration(
            company=company_user.company,
            project_title=title,
        )
    values = {
        "submitted_by": company_user,
        "end_user": end_user,
        "end_user_name": end_user_name,
        "end_user_address": address,
        "bid_date": date(2027, 1, 15),
        "delivery_date": date(2027, 2, 15),
        "contact_person": "Maria Santos",
        "contact_designation": "Procurement Officer",
        "contact_email": "procurement@example.invalid",
        "contact_number": "0000000000",
        "evidence_description": "Development scenario evidence for a specific procurement lot.",
        "evidence_sharing_confirmed": True,
        "status": Registration.Status.SUBMITTED,
        "needs_review": False,
        "opportunity_scope": None,
        "original_submitted_at": submitted_at,
        "version": 1,
    }
    for field, value in values.items():
        setattr(registration, field, value)
    registration.save()
    Registration.objects.filter(pk=registration.pk).update(created_at=submitted_at)

    competitor, _ = CompetitorItem.objects.update_or_create(
        registration=registration,
        brand="Sample Competitor",
        defaults={
            "item_name": "Monochrome laser printer",
            "bid_price": Decimal("8500.00"),
            "remarks": "Development scenario data only.",
        },
    )
    registration.competitor_items.exclude(pk=competitor.pk).delete()
    item, _ = RegistrationItem.objects.update_or_create(
        registration=registration,
        product=product,
        defaults={
            "non_catalog_name": "",
            "quantity": 25,
            "requested_unit_price": Decimal("7950.00"),
            "justification": "Requested scenario price for the public procurement.",
        },
    )
    registration.items.exclude(pk=item.pk).delete()
    RegistrationEvent.objects.get_or_create(
        registration=registration,
        event_type="Submitted",
        defaults={
            "actor": company_user,
            "details": "Development scenario registration submitted.",
            "snapshot": registration_snapshot(registration),
        },
    )
    registration.refresh_from_db()
    return registration


def _confirm_reference_registration(registration, scope, actor):
    registration.status = Registration.Status.ELIGIBLE_MATCHED
    registration.opportunity_scope = scope
    registration.needs_review = False
    registration.save(update_fields=["status", "opportunity_scope", "needs_review"])
    RegistrationReviewDecision.objects.get_or_create(
        registration=registration,
        decision=RegistrationReviewDecision.Decision.CONFIRM_MATCH,
        opportunity_scope=scope,
        defaults={
            "rationale": "Development scenario reference registration.",
            "actor": actor,
            "registration_version": registration.version,
        },
    )


def _base_pair(
    actor,
    *,
    slug,
    opportunity_title,
    end_user_name,
    address,
    scope_name,
    product_code,
):
    product = _product(product_code)
    it_avenue = _company_user("IT Avenue", "deals@itavenue.ph")
    lexmark = _company_user("Lexmark", "deals@lexmark.com")
    scope = _opportunity(
        actor,
        title=opportunity_title,
        end_user_name=end_user_name,
        address=address,
        scope_name=scope_name,
    )
    end_user = scope.opportunity.end_user
    now = timezone.now()
    first = _registration(
        company_user=it_avenue,
        title=f"{slug} reference registration",
        end_user_name=end_user_name,
        address=address,
        product=product,
        submitted_at=now - timedelta(hours=2),
        end_user=end_user,
    )
    _confirm_reference_registration(first, scope, actor)
    second = _registration(
        company_user=lexmark,
        title=f"{slug} later registration",
        end_user_name=end_user_name,
        address=address.replace("Street", "St."),
        product=product,
        submitted_at=now - timedelta(hours=1),
        end_user=end_user,
    )
    return first, second, scope, product


def _result(definition, first, second, suggestion):
    second.refresh_from_db()
    return {
        "scenario": definition,
        "first_reference": first.reference,
        "second_reference": second.reference,
        "second_status": second.get_status_display(),
        "scope": str(second.opportunity_scope) if second.opportunity_scope_id else "Not assigned",
        "suggestion": suggestion.get_outcome_display(),
        "confidence": suggestion.get_confidence_display(),
        "score": suggestion.score,
        "conflicts": suggestion.conflicting_factors,
    }


@transaction.atomic
def load_scenario(key, actor):
    if key not in SCENARIOS:
        raise CommandError("Unknown development scenario.")
    if not actor or not actor.is_superuser:
        raise CommandError("A Django superuser is required to load scenarios.")

    definition = SCENARIOS[key]
    if key == "automatic_exact":
        first, second, _, _ = _base_pair(
            actor,
            slug="QCS printer lot",
            opportunity_title="Quezon City Public Schools Printer Procurement 2027",
            end_user_name="Quezon City Schools Division Office",
            address="Nueva Ecija Street, Bago Bantay, Quezon City",
            scope_name="Lot 1: Monochrome laser printers",
            product_code="M1820W",
        )
        suggestion = generate_matching_suggestion(second)
        return _result(definition, first, second, suggestion)

    if key == "ambiguous_match":
        first, second, _, product = _base_pair(
            actor,
            slug="Pasig printer ambiguity",
            opportunity_title="Pasig Schools Printer Procurement A",
            end_user_name="Pasig City Schools Division Office",
            address="Caruncho Avenue, Pasig City",
            scope_name="Printer lot A",
            product_code="P1820W",
        )
        alternative_scope = _opportunity(
            actor,
            title="Pasig Schools Printer Procurement B",
            end_user_name="Pasig City Schools Division Office",
            address="Caruncho Ave., Pasig City",
            scope_name="Printer lot B",
        )
        alternative = _registration(
            company_user=first.submitted_by,
            title="Pasig printer ambiguity alternative reference",
            end_user_name="Pasig City Schools Division Office",
            address="Caruncho Avenue, Pasig City",
            product=product,
            submitted_at=timezone.now() - timedelta(hours=3),
            end_user=alternative_scope.opportunity.end_user,
        )
        _confirm_reference_registration(alternative, alternative_scope, actor)
        suggestion = generate_matching_suggestion(second)
        return _result(definition, first, second, suggestion)

    first, second, _, _ = _base_pair(
        actor,
        slug="Makati printer edit",
        opportunity_title="Makati City Hall Printer Procurement 2027",
        end_user_name="Makati City General Services Department",
        address="J.P. Rizal Street, Makati City",
        scope_name="Monochrome printer lot",
        product_code="M1820W",
    )
    generate_matching_suggestion(second)
    prior_snapshot = registration_snapshot(second)
    second.end_user_address = "Osmena Boulevard, Cebu City"
    second.status = Registration.Status.REVIEW_REQUIRED
    second.needs_review = True
    second.version += 1
    second.save()
    RegistrationEvent.objects.create(
        registration=second,
        actor=second.submitted_by,
        event_type="Company edit",
        details="Development scenario material address change.",
        snapshot=prior_snapshot,
    )
    suggestion = generate_matching_suggestion(second)
    return _result(definition, first, second, suggestion)


@transaction.atomic
def clear_transactional_records():
    if not settings.DEBUG:
        raise CommandError("Transactional records can only be cleared while DEBUG is true.")
    counts = {
        "review_decisions": RegistrationReviewDecision.objects.count(),
        "registrations": Registration.objects.count(),
        "opportunity_scopes": OpportunityScope.objects.count(),
        "opportunities": Opportunity.objects.count(),
    }
    RegistrationReviewDecision.objects.all().delete()
    Registration.objects.all().delete()
    OpportunityScope.objects.all().delete()
    Opportunity.objects.all().delete()
    return counts
