"""Demo accounts and side deals for guide screenshots. Run with `manage.py shell` on guide_settings.

Only demo companies and test data. The main example deal is entered through the screens by the
capture script, so the screenshots show the real steps.
"""

from datetime import date, timedelta

from django.utils import timezone

from registrations.deadlines import process_deadlines
from registrations.models import (
    Company,
    CompetitorItem,
    EndUser,
    Opportunity,
    OpportunityScope,
    Product,
    ProductPrice,
    Registration,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    User,
)

PASSWORD = "demo-guide-password-1"

partner = Company.objects.create(name="DEMO ONLY - Sample Partner")
second = Company.objects.create(name="DEMO ONLY - Second Partner")
partner_user = User.objects.create_user(
    "demo-partner",
    "demo-partner@example.invalid",
    PASSWORD,
    company=partner,
    first_name="Demo",
    last_name="Partner",
    designation="Account Manager",
    phone_number="09170000000",
)
second_user = User.objects.create_user(
    "demo-partner-2", "demo-partner-2@example.invalid", PASSWORD, company=second
)
admin = User.objects.create_superuser(
    "demo-dbgi",
    "demo-dbgi@example.invalid",
    PASSWORD,
    first_name="DBGI",
    last_name="Reviewer",
    role=User.Role.DBGI_ADMIN,
)

m1820w = Product.objects.get(code="M1820W")
p1820w = Product.objects.get(code="P1820W")
for product, amount in ((m1820w, "10000.00"), (p1820w, "9000.00")):
    ProductPrice.objects.create(
        product=product, unit_price=amount, reason="Starting list price", created_by=admin
    )

lucena = EndUser.objects.create(
    official_name="City of Lucena Mayor's Office",
    government_branch="Local government",
    organization_type="Procuring entity",
    sector="Government",
    region="Region IV-A (CALABARZON)",
    province="Quezon",
    city_municipality="City of Lucena",
    street_address="Lucena City Government Complex, Diversion Road, Barangay Mayao Kanluran",
    postal_code="4301",
    status=EndUser.Status.VERIFIED,
    created_by=admin,
    verified_by=admin,
)


# A separate end-user, so the example deal is not matched to the tied project automatically.
health_office = EndUser.objects.create(
    official_name="Tayabas City Health Office",
    government_branch="Local government",
    organization_type="Procuring entity",
    sector="Health",
    region="Region IV-A (CALABARZON)",
    province="Quezon",
    city_municipality="City of Tayabas",
    street_address="Tayabas City Hall Complex, Barangay Potol",
    postal_code="4327",
    status=EndUser.Status.VERIFIED,
    created_by=admin,
    verified_by=admin,
)


def deal(company, user, title, *, end_user=lucena, product=m1820w, non_catalog="", **fields):
    registration = Registration.objects.create(
        company=company,
        submitted_by=user,
        end_user=end_user,
        end_user_name=end_user.official_name,
        end_user_address=end_user.full_address,
        project_title=title,
        bid_date=date(2026, 12, 15),
        delivery_date=date(2027, 2, 1),
        contact_person="Demo Partner",
        contact_designation="Account Manager",
        contact_email=user.email,
        contact_number="09170000000",
        evidence_description="Request for quotation from the office.",
        evidence_sharing_confirmed=True,
        **fields,
    )
    CompetitorItem.objects.create(
        registration=registration,
        brand="Canon",
        item_name="imageCLASS LBP246dw",
        bid_price="9300.00",
    )
    item = RegistrationItem.objects.create(
        registration=registration,
        product=None if non_catalog else product,
        non_catalog_name=non_catalog,
        quantity=5,
        requested_unit_price="9000.00",
    )
    if not non_catalog:
        item.list_unit_price_snapshot = product.prices.first().unit_price
        item.price_version = product.prices.first()
        item.save()
        RegistrationCategoryApproval.objects.create(
            registration=registration, category=product.category
        )
    RegistrationEvent.objects.create(
        registration=registration,
        actor=user,
        event_type="Submitted",
        details="Registration submitted.",
    )
    return registration


deal(partner, partner_user, "Printers for the Lucena City Library")
deal(
    partner,
    partner_user,
    "Scanners for the City Treasurer's Office",
    non_catalog="High-speed document scanner",
)

opportunity = Opportunity.objects.create(
    title="Printers for the Tayabas City Health Office",
    end_user=health_office,
    end_user_name=health_office.official_name,
    end_user_address=health_office.full_address,
    created_by=admin,
)
scope = OpportunityScope.objects.create(
    opportunity=opportunity, name="Whole opportunity", scope_type=OpportunityScope.ScopeType.WHOLE
)
tied_time = timezone.now() - timedelta(days=3)
for company, user in ((partner, partner_user), (second, second_user)):
    deal(
        company,
        user,
        "Printers for the Tayabas City Health Office",
        end_user=health_office,
        product=p1820w,
        status=Registration.Status.ELIGIBLE_MATCHED,
        opportunity_scope=scope,
        original_submitted_at=tied_time,
    )

old = deal(
    partner,
    partner_user,
    "Printers for the City Engineer's Office",
    original_submitted_at=timezone.now() - timedelta(days=54),
)
process_deadlines()
print("seeded", Registration.objects.count(), "deals")
