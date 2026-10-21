from django.db import transaction

from .models import (
    Opportunity,
    OpportunityScope,
    PriceApprovalRenewal,
    Registration,
    RegistrationCategoryApproval,
    RegistrationItemApproval,
    RegistrationReviewDecision,
)


def transactional_record_counts():
    return {
        "registrations": Registration.objects.count(),
        "review_decisions": RegistrationReviewDecision.objects.count(),
        "item_approvals": RegistrationItemApproval.objects.count(),
        "category_approvals": RegistrationCategoryApproval.objects.count(),
        "price_renewals": PriceApprovalRenewal.objects.count(),
        "opportunity_scopes": OpportunityScope.objects.count(),
        "opportunities": Opportunity.objects.count(),
    }


@transaction.atomic
def clear_transactional_records():
    counts = transactional_record_counts()

    PriceApprovalRenewal.objects.all().delete()
    RegistrationItemApproval.objects.all().delete()
    RegistrationCategoryApproval.objects.all().delete()
    RegistrationReviewDecision.objects.all().delete()
    Registration.objects.all().delete()
    OpportunityScope.objects.all().delete()
    Opportunity.objects.all().delete()

    return counts
