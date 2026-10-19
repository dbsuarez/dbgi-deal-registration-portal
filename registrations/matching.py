import re
from difflib import SequenceMatcher

from django.db import transaction

from .models import MatchingSuggestion, OpportunityScope

RULE_VERSION = "matching-v1"


def _normalize(value):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", value.lower()).split())


def _similarity(left, right):
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def generate_matching_suggestion(registration):
    scopes = OpportunityScope.objects.filter(
        is_active=True, opportunity__is_active=True
    ).select_related("opportunity")
    requested_products = set(
        registration.items.exclude(product_id=None).values_list("product_id", flat=True)
    )
    best = None
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
        score = round(name_score * 45 + address_score * 30 + (25 if product_overlap else 0))
        candidate = (score, name_score, address_score, product_overlap, scope)
        if best is None or candidate[0] > best[0]:
            best = candidate

    factors = []
    conflicts = []
    candidate_scope = None
    if best is None:
        outcome = MatchingSuggestion.Outcome.DIFFERENT
        confidence = MatchingSuggestion.Confidence.LOW
        score = 0
        conflicts.append("No existing opportunity scope is available for comparison.")
    else:
        score, name_score, address_score, product_overlap, candidate_scope = best
        if name_score >= 0.8:
            factors.append("The end-user names closely match.")
        else:
            conflicts.append("The end-user names do not closely match.")
        if address_score >= 0.65:
            factors.append("The end-user addresses appear related.")
        else:
            conflicts.append("The end-user addresses have limited similarity.")
        if product_overlap:
            factors.append("One or more requested catalog products overlap.")
        else:
            conflicts.append("No requested catalog product overlap was found.")

        if score >= 75:
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
        return MatchingSuggestion.objects.create(
            registration=registration,
            candidate_scope=candidate_scope,
            outcome=outcome,
            confidence=confidence,
            score=score,
            supporting_factors=factors,
            conflicting_factors=conflicts,
            rule_version=RULE_VERSION,
        )
