"""Opportunity rankings: first eligible submission wins; DBGI settles exact ties (decision B5)."""

from collections import defaultdict
from dataclasses import dataclass
from itertools import groupby

from .models import ProjectChange, RankingTieDecision, Registration


@dataclass
class RankedEntry:
    registration: Registration
    rank: int
    is_tied: bool
    tie_decision: RankingTieDecision | None = None


def ranked_registrations(scope_ids):
    """Per scope, each company's earliest Registered registration, earliest first."""
    registrations = (
        Registration.objects.filter(
            status=Registration.Status.ELIGIBLE_MATCHED,
            opportunity_scope_id__in=scope_ids,
        )
        .select_related("company")
        .order_by("opportunity_scope_id", "original_submitted_at", "id")
    )
    by_scope = defaultdict(list)
    seen_companies = set()
    for registration in registrations:
        company_key = (registration.opportunity_scope_id, registration.company_id)
        if company_key not in seen_companies:
            seen_companies.add(company_key)
            by_scope[registration.opportunity_scope_id].append(registration)
    return by_scope


def latest_tie_decisions(scope_ids):
    """The decision in force for each (scope, tied time): the most recent one."""
    decisions = RankingTieDecision.objects.filter(opportunity_scope_id__in=scope_ids).order_by(
        "decided_at", "id"
    )
    return {(item.opportunity_scope_id, item.submitted_at): item for item in decisions}


def latest_rank_orders(scope_ids):
    """The order DBGI set when it last merged a project into each scope, if any (decision B3)."""
    merges = ProjectChange.objects.filter(
        kind=ProjectChange.Kind.MERGE, target_scope_id__in=scope_ids
    ).order_by("decided_at", "id")
    return {merge.target_scope_id: merge.rank_order for merge in merges}


def rank_scope(scope_id, registrations, decisions, rank_order=None):
    """Rank one scope. Tied registrations share a rank until a decision orders all of them; if a
    company joins the tie later, the tie reopens. Companies that left no longer matter. An order
    DBGI set in a merge comes first; anyone confirmed later follows by submission time."""
    placed = {registration_id: index for index, registration_id in enumerate(rank_order or [])}
    listed = sorted(
        (item for item in registrations if item.pk in placed), key=lambda item: placed[item.pk]
    )
    entries = [RankedEntry(item, index + 1, False) for index, item in enumerate(listed)]
    position = len(entries) + 1
    remaining = [item for item in registrations if item.pk not in placed]
    for submitted_at, group in groupby(remaining, key=lambda item: item.original_submitted_at):
        group = list(group)
        decision = decisions.get((scope_id, submitted_at)) if len(group) > 1 else None
        if decision and {item.pk for item in group} <= set(decision.order):
            group.sort(key=lambda item: decision.order.index(item.pk))
            entries += [
                RankedEntry(item, position + index, False, decision)
                for index, item in enumerate(group)
            ]
        else:
            entries += [RankedEntry(item, position, len(group) > 1) for item in group]
        position += len(group)
    return entries
