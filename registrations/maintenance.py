from django.db import transaction

from .models import (
    Opportunity,
    OpportunityScope,
    PriceApprovalRenewal,
    ProjectChange,
    ProjectOutcomeReport,
    RankingTieDecision,
    Registration,
    RegistrationCategoryApproval,
    RegistrationItemApproval,
    RegistrationReviewDecision,
    RepeatOrder,
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
        "repeat_orders": RepeatOrder.objects.count(),
        "outcome_reports": ProjectOutcomeReport.objects.count(),
        "tie_decisions": RankingTieDecision.objects.count(),
        "project_changes": ProjectChange.objects.count(),
    }


@transaction.atomic
def clear_transactional_records():
    counts = transactional_record_counts()

    # Stored letters are removed only if the whole clear succeeds.
    letters = [
        stored
        for repeat_order in RepeatOrder.objects.all()
        for stored in (repeat_order.noa_file, repeat_order.ntp_file)
    ]
    RepeatOrder.objects.all().delete()
    for stored in letters:
        transaction.on_commit(lambda stored=stored: stored.storage.delete(stored.name))
    ProjectChange.objects.all().delete()
    RankingTieDecision.objects.all().delete()
    ProjectOutcomeReport.objects.all().delete()
    PriceApprovalRenewal.objects.all().delete()
    RegistrationItemApproval.objects.all().delete()
    RegistrationCategoryApproval.objects.all().delete()
    RegistrationReviewDecision.objects.all().delete()
    Registration.objects.all().delete()
    OpportunityScope.objects.all().delete()
    Opportunity.objects.all().delete()

    return counts
