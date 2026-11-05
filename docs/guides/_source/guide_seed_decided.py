"""Extra demo deals for the merge, split, and repeat order screens. Run after guide_seed.py."""

from datetime import timedelta

from django.utils import timezone

from registrations.models import (
    Company,
    CompetitorItem,
    EndUser,
    Opportunity,
    OpportunityScope,
    Product,
    Registration,
    RegistrationCategoryApproval,
    RegistrationItem,
    RegistrationItemApproval,
    User,
)

partner = Company.objects.get(name="DEMO ONLY - Sample Partner")
second = Company.objects.get(name="DEMO ONLY - Second Partner")
partner_user = User.objects.get(username="demo-partner")
second_user = User.objects.get(username="demo-partner-2")
admin = User.objects.get(username="demo-dbgi")
lucena = EndUser.objects.get(official_name="City of Lucena Mayor's Office")
m1820w = Product.objects.get(code="M1820W")
p1820w = Product.objects.get(code="P1820W")


def project(title):
    opportunity = Opportunity.objects.create(
        title=title,
        end_user=lucena,
        end_user_name=lucena.official_name,
        end_user_address=lucena.full_address,
        created_by=admin,
    )
    return OpportunityScope.objects.create(
        opportunity=opportunity,
        name="Whole opportunity",
        scope_type=OpportunityScope.ScopeType.WHOLE,
    )


def deal(company, user, title, scope, products, days_ago, approve=False):
    registration = Registration.objects.create(
        company=company,
        submitted_by=user,
        end_user=lucena,
        end_user_name=lucena.official_name,
        end_user_address=lucena.full_address,
        project_title=title,
        bid_date=timezone.localdate() + timedelta(days=40),
        delivery_date=timezone.localdate() + timedelta(days=90),
        contact_person="Demo Partner",
        contact_designation="Account Manager",
        contact_email=user.email,
        contact_number="09170000000",
        evidence_description="Request for quotation from the office.",
        evidence_sharing_confirmed=True,
        status=Registration.Status.ELIGIBLE_MATCHED,
        opportunity_scope=scope,
        original_submitted_at=timezone.now() - timedelta(days=days_ago),
    )
    CompetitorItem.objects.create(
        registration=registration, brand="Canon", item_name="imageCLASS", bid_price="9300.00"
    )
    approvals = {}
    for product, quantity in products:
        item = RegistrationItem.objects.create(
            registration=registration,
            product=product,
            quantity=quantity,
            requested_unit_price="8000.00",
            list_unit_price_snapshot=product.prices.first().unit_price,
            price_version=product.prices.first(),
        )
        approval = approvals.get(product.category)
        if approval is None:
            approval = RegistrationCategoryApproval.objects.create(
                registration=registration,
                category=product.category,
                status=(
                    RegistrationCategoryApproval.Status.APPROVED
                    if approve
                    else RegistrationCategoryApproval.Status.PENDING
                ),
                rationale="Within the allowed discount." if approve else "",
                reviewed_by=admin if approve else None,
                reviewed_at=timezone.now() if approve else None,
                valid_until=timezone.localdate() + timedelta(days=60) if approve else None,
            )
            approvals[product.category] = approval
        if approve:
            RegistrationItemApproval.objects.create(
                category_approval=approval, registration_item=item, approved_unit_price="8000.00"
            )
    return registration


deal(
    partner,
    partner_user,
    "Repeat order example: printers for the Mayor's Office",
    project("Printers bought last year"),
    [(m1820w, 10)],
    30,
    approve=True,
)
deal(
    partner,
    partner_user,
    "Split example: printers in two lots",
    project("Printers in two lots"),
    [(m1820w, 10), (p1820w, 4)],
    20,
    approve=True,
)
deal(
    partner,
    partner_user,
    "Merge example: first project",
    project("Merge example: main project"),
    [(m1820w, 5)],
    15,
)
deal(
    second,
    second_user,
    "Merge example: second project",
    project("Merge example: same tender"),
    [(p1820w, 5)],
    10,
)
print("seeded decided-rule examples")
