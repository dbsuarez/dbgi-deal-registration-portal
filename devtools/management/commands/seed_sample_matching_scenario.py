from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
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


class Command(BaseCommand):
    help = "Create a local two-company opportunity-matching demonstration."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Sample scenarios can only be seeded when DEBUG is enabled.")

        admin = User.objects.filter(username="admin-preview", is_active=True).first()
        if not admin or not admin.is_dbgi_admin:
            raise CommandError("Run seed_development_accounts before this command.")

        product, _ = Product.objects.get_or_create(
            code="M1820W",
            defaults={
                "name": "20 ppm monochrome laser printer",
                "category": "Laser Printers",
            },
        )
        it_avenue = self._company_user("IT Avenue", "deals@itavenue.ph")
        lexmark = self._company_user("Lexmark", "deals@lexmark.com")

        end_user, _ = EndUser.objects.update_or_create(
            official_name="Quezon City Schools Division Office",
            defaults={
                "city_municipality": "Quezon City",
                "street_address": "Nueva Ecija Street, Bago Bantay",
                "status": EndUser.Status.VERIFIED,
                "is_active": True,
                "created_by": admin,
                "verified_by": admin,
                "verified_at": timezone.now(),
            },
        )

        opportunity, _ = Opportunity.objects.update_or_create(
            title="Quezon City Public Schools Printer Procurement 2027",
            defaults={
                "end_user_name": "Quezon City Schools Division Office",
                "end_user_address": "Nueva Ecija Street, Bago Bantay, Quezon City",
                "end_user": end_user,
                "is_active": True,
                "created_by": admin,
            },
        )
        scope, _ = OpportunityScope.objects.update_or_create(
            opportunity=opportunity,
            name="Lot 1: Monochrome laser printers",
            defaults={
                "scope_type": OpportunityScope.ScopeType.LOT,
                "description": "Supply and delivery of monochrome laser printers.",
                "is_active": True,
            },
        )

        first_time = timezone.now() - timedelta(hours=2)
        second_time = timezone.now() - timedelta(hours=1)
        first = self._registration(
            company=it_avenue.company,
            user=it_avenue,
            title="QCS Division Office laser printer acquisition",
            end_user_name="Quezon City Schools Division Office",
            address="Nueva Ecija Street, Bago Bantay, Quezon City",
            product=product,
            submitted_at=first_time,
            end_user=end_user,
        )
        first.status = Registration.Status.ELIGIBLE_MATCHED
        first.opportunity_scope = scope
        first.needs_review = False
        first.save(update_fields=["status", "opportunity_scope", "needs_review"])
        RegistrationReviewDecision.objects.get_or_create(
            registration=first,
            decision=RegistrationReviewDecision.Decision.CONFIRM_MATCH,
            defaults={
                "opportunity_scope": scope,
                "rationale": "Evidence identifies this procurement and Lot 1 specifically.",
                "actor": admin,
                "registration_version": first.version,
            },
        )

        second = self._registration(
            company=lexmark.company,
            user=lexmark,
            title="Quezon City SDO monochrome printer project",
            end_user_name="Quezon City Schools Division Office",
            address="Nueva Ecija St., Bago Bantay, Quezon City",
            product=product,
            submitted_at=second_time,
            end_user=end_user,
        )
        second.status = Registration.Status.SUBMITTED
        second.opportunity_scope = None
        second.needs_review = False
        second.save(update_fields=["status", "opportunity_scope", "needs_review"])
        suggestion = generate_matching_suggestion(second)

        self.stdout.write(self.style.SUCCESS("Sample matching scenario is ready."))
        self.stdout.write(f"IT Avenue: {first.reference} at {first.original_submitted_at}")
        self.stdout.write(f"Lexmark: {second.reference} at {second.original_submitted_at}")
        self.stdout.write(
            f"Suggestion: {suggestion.get_outcome_display()} "
            f"({suggestion.get_confidence_display()}, {suggestion.score}%)"
        )
        second.refresh_from_db()
        self.stdout.write(
            f"Result: {second.get_status_display()} in {second.opportunity_scope} "
            "without administrator intervention."
        )

    def _company_user(self, company_name, email):
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

    def _registration(
        self,
        *,
        company,
        user,
        title,
        end_user_name,
        address,
        product,
        submitted_at,
        end_user,
    ):
        registration, created = Registration.objects.get_or_create(
            company=company,
            project_title=title,
            defaults={
                "submitted_by": user,
                "end_user": end_user,
                "end_user_name": end_user_name,
                "end_user_address": address,
                "bid_date": date(2027, 1, 15),
                "delivery_date": date(2027, 2, 15),
                "contact_person": "Maria Santos",
                "contact_designation": "Procurement Officer",
                "contact_email": "procurement@example.invalid",
                "contact_number": "0000000000",
                "evidence_description": "Public procurement planning document for Lot 1.",
                "evidence_sharing_confirmed": True,
                "original_submitted_at": submitted_at,
            },
        )
        if created:
            CompetitorItem.objects.create(
                registration=registration,
                brand="Sample Competitor",
                item_name="Monochrome laser printer",
                bid_price=Decimal("8500.00"),
                remarks="Demonstration data only.",
            )
            RegistrationItem.objects.create(
                registration=registration,
                product=product,
                quantity=25,
                requested_unit_price=Decimal("7950.00"),
                justification="Requested project price for the public-school procurement.",
            )
            RegistrationEvent.objects.create(
                registration=registration,
                actor=user,
                event_type="Submitted",
                details="Sample scenario registration submitted.",
                snapshot=registration_snapshot(registration),
            )
        Registration.objects.filter(pk=registration.pk).update(
            created_at=submitted_at,
            original_submitted_at=submitted_at,
        )
        registration.refresh_from_db()
        return registration
