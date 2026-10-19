import re
from difflib import SequenceMatcher

from django.db import transaction

from .audit import registration_snapshot
from .models import EndUser, MatchingSuggestion, OpportunityScope, Registration, RegistrationEvent

RULE_VERSION = "matching-v2"
ADDRESS_ALIASES = {
    "ave": "avenue",
    "rd": "road",
    "st": "street",
}
AUTO_MATCHABLE_STATUSES = {
    Registration.Status.SUBMITTED,
    Registration.Status.RESUBMITTED,
    Registration.Status.REVIEW_REQUIRED,
}


def _normalize(value):
    tokens = re.sub(r"[^a-z0-9 ]", " ", value.lower()).split()
    return " ".join(ADDRESS_ALIASES.get(token, token) for token in tokens)


def _similarity(left, right):
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def generate_matching_suggestion(registration):
    if not registration.end_user_id or registration.end_user.status != EndUser.Status.VERIFIED:
        with transaction.atomic():
            MatchingSuggestion.objects.filter(registration=registration, is_current=True).update(
                is_current=False
            )
            return MatchingSuggestion.objects.create(
                registration=registration,
                outcome=MatchingSuggestion.Outcome.CLARIFY,
                confidence=MatchingSuggestion.Confidence.LOW,
                score=0,
                supporting_factors=[],
                conflicting_factors=[
                    "The selected End-user is awaiting administrator verification."
                ],
                rule_version=RULE_VERSION,
            )
    scopes = OpportunityScope.objects.filter(
        is_active=True,
        opportunity__is_active=True,
        opportunity__end_user__status=EndUser.Status.VERIFIED,
    ).select_related("opportunity")
    requested_products = set(
        registration.items.exclude(product_id=None).values_list("product_id", flat=True)
    )
    candidates = []
    for scope in scopes:
        name_score = _similarity(registration.end_user_name, scope.opportunity.end_user_name)
        address_score = _similarity(
            registration.end_user_address, scope.opportunity.end_user_address
        )
        existing_products = set(
            scope.registrations.exclude(pk=registration.pk)
            .filter(items__product_id__isnull=False)
            .values_list("items__product_id", flat=True)
        )
        product_overlap = bool(requested_products & existing_products)
        complete_product_overlap = bool(requested_products) and requested_products.issubset(
            existing_products
        )
        score = round(name_score * 45 + address_score * 30 + (25 if product_overlap else 0))
        candidates.append(
            (
                score,
                name_score,
                address_score,
                product_overlap,
                complete_product_overlap,
                scope,
            )
        )

    best = max(candidates, key=lambda candidate: candidate[0], default=None)
    exact_candidates = [
        candidate
        for candidate in candidates
        if candidate[1] == 1 and candidate[2] == 1 and candidate[4]
    ]

    factors = []
    conflicts = []
    candidate_scope = None
    if best is None:
        outcome = MatchingSuggestion.Outcome.DIFFERENT
        confidence = MatchingSuggestion.Confidence.LOW
        score = 0
        conflicts.append("No existing opportunity scope is available for comparison.")
    else:
        (
            score,
            name_score,
            address_score,
            product_overlap,
            complete_product_overlap,
            candidate_scope,
        ) = best
        if name_score == 1:
            factors.append("The normalized end-user names match exactly.")
        elif name_score >= 0.8:
            factors.append("The end-user names closely match.")
        else:
            conflicts.append("The end-user names do not closely match.")
        if address_score == 1:
            factors.append("The normalized end-user addresses match exactly.")
        elif address_score >= 0.65:
            factors.append("The end-user addresses appear related.")
        else:
            conflicts.append("The end-user addresses have limited similarity.")
        if complete_product_overlap:
            factors.append("All requested catalog products overlap.")
        elif product_overlap:
            factors.append("One or more requested catalog products overlap.")
        else:
            conflicts.append("No requested catalog product overlap was found.")

        if len(exact_candidates) > 1:
            outcome = MatchingSuggestion.Outcome.CLARIFY
            confidence = MatchingSuggestion.Confidence.MEDIUM
            conflicts.append("More than one opportunity scope is an exact match.")
        elif score >= 75:
            outcome = MatchingSuggestion.Outcome.SAME_SCOPE
            confidence = MatchingSuggestion.Confidence.HIGH
        elif score >= 50:
            outcome = MatchingSuggestion.Outcome.CLARIFY
            confidence = MatchingSuggestion.Confidence.MEDIUM
        elif name_score >= 0.8:
            outcome = MatchingSuggestion.Outcome.NEW_SCOPE
            confidence = MatchingSuggestion.Confidence.MEDIUM
        else:
            outcome = MatchingSuggestion.Outcome.DIFFERENT
            confidence = MatchingSuggestion.Confidence.LOW

    with transaction.atomic():
        MatchingSuggestion.objects.filter(registration=registration, is_current=True).update(
            is_current=False
        )
        suggestion = MatchingSuggestion.objects.create(
            registration=registration,
            candidate_scope=candidate_scope,
            outcome=outcome,
            confidence=confidence,
            score=score,
            supporting_factors=factors,
            conflicting_factors=conflicts,
            rule_version=RULE_VERSION,
        )
        if (
            len(exact_candidates) == 1
            and candidate_scope == exact_candidates[0][5]
            and not conflicts
            and registration.status in AUTO_MATCHABLE_STATUSES
        ):
            prior_snapshot = registration_snapshot(registration)
            registration.status = Registration.Status.ELIGIBLE_MATCHED
            registration.opportunity_scope = candidate_scope
            registration.needs_review = False
            registration.version += 1
            registration.save()
            RegistrationEvent.objects.create(
                registration=registration,
                actor=None,
                event_type="Automatically matched",
                details=(
                    f"{RULE_VERSION} linked this registration to {candidate_scope} because "
                    "one scope had an exact normalized end-user and address match, all "
                    "requested catalog products overlapped, and no conflicts were found."
                ),
                snapshot=prior_snapshot,
            )
        return suggestion
