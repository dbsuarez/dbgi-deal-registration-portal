"""The price rule: rank 1 gets the best price, and everyone else gets the same price as each other.

DBGI still decides each price, so a broken rule is a warning and never blocks the decision.
"""

from .models import Registration, RegistrationCategoryApproval, RegistrationItemApproval
from .ranking import latest_rank_orders, latest_tie_decisions, rank_scope, ranked_registrations

ACTIVE_STATUSES = {
    RegistrationCategoryApproval.Status.APPROVED,
    RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
}


def _entries(scope_id):
    return rank_scope(
        scope_id,
        ranked_registrations([scope_id])[scope_id],
        latest_tie_decisions([scope_id]),
        latest_rank_orders([scope_id]).get(scope_id),
    )


def _rank_text(entry):
    return f"Tied {entry.rank}" if entry.is_tied else str(entry.rank)


def rank_text(registration):
    """The deal's place on its project, in words."""
    if (
        not registration.opportunity_scope_id
        or registration.status != Registration.Status.ELIGIBLE_MATCHED
    ):
        return "Not ranked: only Registered deals have a rank."
    for entry in _entries(registration.opportunity_scope_id):
        if entry.registration.pk == registration.pk:
            return _rank_text(entry)
    return "Not counted: this company has an earlier deal on this project."


def _prices(registration_ids):
    """Valid approved prices as {registration id: {product id: (price, product name)}}."""
    prices = {}
    rows = RegistrationItemApproval.objects.filter(
        registration_item__registration_id__in=registration_ids,
        registration_item__product__isnull=False,
        approved_unit_price__isnull=False,
    ).select_related("category_approval", "registration_item__product")
    for row in rows:
        if row.category_approval.effective_status not in ACTIVE_STATUSES:
            continue
        item = row.registration_item
        prices.setdefault(item.registration_id, {})[item.product_id] = (
            row.approved_unit_price,
            item.product.name,
        )
    return prices


def project_price_rows(registration):
    """Every valid approved price on the deal's project, in rank order, for the price form."""
    if not registration.opportunity_scope_id:
        return []
    entries = _entries(registration.opportunity_scope_id)
    prices = _prices([entry.registration.pk for entry in entries])
    return [
        {
            "rank": _rank_text(entry),
            "company": entry.registration.company.name,
            "reference": entry.registration.reference,
            "product": name,
            "price": f"{price:,.2f}",
        }
        for entry in entries
        for price, name in prices.get(entry.registration.pk, {}).values()
    ]


def price_warnings(approval):
    """What breaks the price rule on this decision. Empty when nothing can be compared."""
    registration = approval.registration
    if approval.status not in ACTIVE_STATUSES or not registration.opportunity_scope_id:
        return []
    entries = _entries(registration.opportunity_scope_id)
    own = next((entry for entry in entries if entry.registration.pk == registration.pk), None)
    if own is None:
        return []
    prices = _prices([entry.registration.pk for entry in entries])
    warnings = []
    for product_id, (price, name) in prices.get(registration.pk, {}).items():
        for other in entries:
            if other is own or product_id not in prices.get(other.registration.pk, {}):
                continue
            other_price = prices[other.registration.pk][product_id][0]
            company = other.registration.company.name
            compared = (
                f"{name}: this deal (rank {_rank_text(own)}) is {price:,.2f}, and {company} "
                f"(rank {_rank_text(other)}) is {other_price:,.2f}."
            )
            if own.rank == 1 and other.rank == 1:
                warnings.append(
                    f"Decide the tie first, so rank 1 can have the best price. {compared}"
                )
            elif (own.rank == 1 and price >= other_price) or (
                other.rank == 1 and other_price >= price
            ):
                warnings.append(f"Rank 1 should have the best price. {compared}")
            elif own.rank != 1 and other.rank != 1 and price != other_price:
                warnings.append(f"Everyone after rank 1 should have the same price. {compared}")
    return warnings
