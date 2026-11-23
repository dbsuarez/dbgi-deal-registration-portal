"""The owner's overview: what needs him, how the month is going, and what is coming or stuck.

Kept short on purpose: a few numbers and lists of at most five rows, never a feed of every step.
The overview page and the Monday summary email both use owner_overview(), so they always agree.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import (
    Opportunity,
    Product,
    ProjectOutcomeReport,
    Registration,
    RegistrationCategoryApproval,
    RegistrationItemApproval,
)

LIST_SIZE = 5
UPCOMING_DAYS = 14
STUCK_REVIEW_DAYS = 7
STUCK_OWNER_DAYS = 2
THIN_MARGIN_PERCENT = Decimal("5")
ENDING_DAYS = 14
ACTIVE_PRICES = {
    RegistrationCategoryApproval.Status.APPROVED,
    RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
}
OPEN_STATUSES = set(Registration.Status) - {
    Registration.Status.CLOSED,
    Registration.Status.REJECTED,
}
WAITING_ON_DBGI = {
    Registration.Status.SUBMITTED,
    Registration.Status.RESUBMITTED,
    Registration.Status.REVIEW_REQUIRED,
    Registration.Status.UNDER_REVIEW,
}
CLOSED_PROJECTS = {
    Opportunity.ProjectStatus.WON,
    Opportunity.ProjectStatus.LOST,
    Opportunity.ProjectStatus.CANCELLED,
}


def _month_start(day):
    return day.replace(day=1)


def _previous_month_start(day):
    return (_month_start(day) - timedelta(days=1)).replace(day=1)


def _quarter_start(day):
    return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)


def deal_value(registration):
    """The deal's total: the approved price where there is one, the requested price otherwise."""
    total = Decimal("0.00")
    for item in registration.items.all():
        approval = getattr(item, "price_approval", None)
        price = (
            approval.approved_unit_price
            if approval is not None
            and approval.approved_unit_price is not None
            and approval.category_approval.status
            in {
                RegistrationCategoryApproval.Status.APPROVED,
                RegistrationCategoryApproval.Status.PARTIALLY_APPROVED,
            }
            else item.requested_unit_price
        )
        total += price * item.quantity
    return total.quantize(Decimal("0.01"))


def _deals():
    return Registration.objects.select_related(
        "company", "opportunity_scope__opportunity"
    ).prefetch_related("items__price_approval__category_approval")


def _between(field, start, end):
    return {f"{field}__date__gte": start, f"{field}__date__lt": end}


def _outcomes(outcomes, start, end):
    return ProjectOutcomeReport.objects.filter(
        status=ProjectOutcomeReport.Status.CONFIRMED,
        outcome__in=outcomes,
        **_between("decided_at", start, end),
    )


def _average_discount(start, end):
    """The discount from the list price on prices approved between `start` and `end`, weighted by
    value (a big order counts more). None when nothing was approved."""
    rows = RegistrationItemApproval.objects.filter(
        approved_unit_price__isnull=False,
        category_approval__status__in=ACTIVE_PRICES,
        **_between("category_approval__reviewed_at", start, end),
    ).select_related("registration_item")
    listed = approved = Decimal("0")
    for row in rows:
        item = row.registration_item
        if item.list_unit_price_snapshot > 0:
            listed += item.list_unit_price_snapshot * item.quantity
            approved += row.approved_unit_price * item.quantity
    return round((listed - approved) * 100 / listed, 2) if listed else None


def _thin_margins(today):
    """Approved prices less than THIN_MARGIN_PERCENT above the landed cost, on open deals."""
    rows = (
        RegistrationItemApproval.objects.filter(
            approved_unit_price__isnull=False,
            category_approval__status__in=ACTIVE_PRICES,
            registration_item__product__isnull=False,
            registration_item__registration__status__in=OPEN_STATUSES,
        )
        .exclude(category_approval__valid_until__lt=today)
        .select_related("registration_item__product", "registration_item__registration__company")
    )
    costs = dict(
        Product.objects.filter(pk__in=[row.registration_item.product_id for row in rows])
        .with_landed_cost()
        .values_list("pk", "landed_cost")
    )
    thin = []
    for row in rows:
        item = row.registration_item
        cost = costs.get(item.product_id)
        if not cost:
            continue
        margin = (row.approved_unit_price - cost) * 100 / cost
        if margin < THIN_MARGIN_PERCENT:
            deal = item.registration
            thin.append(
                {
                    "registration_id": deal.pk,
                    "reference": deal.reference,
                    "company_name": deal.company.name,
                    "product": item.display_name,
                    "approved_price": row.approved_unit_price,
                    "landed_cost": Decimal(cost).quantize(Decimal("0.01")),
                    "margin_percent": round(margin, 2),
                }
            )
    return sorted(thin, key=lambda row: row["margin_percent"])


def owner_overview(today=None):
    today = today or timezone.localdate()
    this_month = _month_start(today)
    last_month = _previous_month_start(today)
    next_month = (this_month + timedelta(days=32)).replace(day=1)
    now = timezone.now()

    def won(start, end):
        reports = _outcomes([ProjectOutcomeReport.Outcome.WON], start, end).select_related(
            "registration"
        )
        deals = _deals().filter(pk__in=reports.values("registration_id"))
        return reports.count(), sum((deal_value(deal) for deal in deals), Decimal("0.00"))

    def lost(start, end):
        return _outcomes(
            [ProjectOutcomeReport.Outcome.LOST, ProjectOutcomeReport.Outcome.CANCELLED], start, end
        ).count()

    won_count, won_value = won(this_month, next_month)
    won_prev_count, won_prev_value = won(last_month, this_month)
    pipeline = (
        _deals()
        .filter(status__in=OPEN_STATUSES)
        .exclude(opportunity_scope__opportunity__project_status__in=CLOSED_PROJECTS)
    )

    waiting_for_owner = RegistrationCategoryApproval.objects.filter(
        status=RegistrationCategoryApproval.Status.OWNER_REVIEW
    ).exclude(registration__status=Registration.Status.CLOSED)

    upcoming = list(
        _deals()
        .filter(
            status__in=OPEN_STATUSES,
            bid_date__gte=today,
            bid_date__lte=today + timedelta(days=UPCOMING_DAYS),
        )
        .order_by("bid_date", "id")
    )
    undecided = {
        RegistrationCategoryApproval.Status.PENDING,
        RegistrationCategoryApproval.Status.CHANGES_REQUESTED,
        RegistrationCategoryApproval.Status.OWNER_REVIEW,
    }

    stuck_reviews = list(
        _deals()
        .filter(
            status__in=WAITING_ON_DBGI,
            updated_at__lt=now - timedelta(days=STUCK_REVIEW_DAYS),
        )
        .order_by("updated_at")
    )
    stuck_prices = list(
        waiting_for_owner.filter(reviewed_at__lt=now - timedelta(days=STUCK_OWNER_DAYS))
        .select_related("registration__company")
        .order_by("reviewed_at")
    )

    wins = list(
        ProjectOutcomeReport.objects.filter(
            status=ProjectOutcomeReport.Status.CONFIRMED, outcome=ProjectOutcomeReport.Outcome.WON
        )
        .select_related("registration__company")
        .order_by("-decided_at", "-id")[:LIST_SIZE]
    )
    win_values = {
        deal.pk: deal_value(deal)
        for deal in _deals().filter(pk__in=[report.registration_id for report in wins])
    }

    quarter = _quarter_start(today)
    quarter_reports = ProjectOutcomeReport.objects.filter(
        status=ProjectOutcomeReport.Status.CONFIRMED, decided_at__date__gte=quarter
    )
    quarter_won = quarter_reports.filter(outcome=ProjectOutcomeReport.Outcome.WON).count()
    quarter_lost = quarter_reports.filter(outcome=ProjectOutcomeReport.Outcome.LOST).count()
    thin = _thin_margins(today)
    ending = list(
        RegistrationCategoryApproval.objects.filter(
            status__in=ACTIVE_PRICES,
            valid_until__gte=today,
            valid_until__lte=today + timedelta(days=ENDING_DAYS),
            registration__status__in=OPEN_STATUSES,
            registration__bid_date__gte=today,
        )
        .select_related("registration__company")
        .order_by("valid_until", "id")
    )
    partners = {}
    for deal in _deals().filter(status__in=OPEN_STATUSES, created_at__date__gte=quarter):
        name = deal.company.name
        count, value = partners.get(name, (0, Decimal("0.00")))
        partners[name] = (count + 1, value + deal_value(deal))
    top_partners = sorted(partners.items(), key=lambda row: (-row[1][1], row[0]))[:LIST_SIZE]

    def deal_row(deal, **extra):
        return {
            "registration_id": deal.pk,
            "reference": deal.reference,
            "company_name": deal.company.name,
            "project_title": deal.project_title,
            **extra,
        }

    return {
        "today": today,
        "waiting_for_owner": waiting_for_owner.count(),
        "month": {
            "label": this_month.strftime("%B %Y"),
            "new_deals": Registration.objects.filter(
                **_between("created_at", this_month, next_month)
            ).count(),
            "new_deals_last_month": Registration.objects.filter(
                **_between("created_at", last_month, this_month)
            ).count(),
            "won": won_count,
            "won_value": won_value,
            "won_last_month": won_prev_count,
            "won_value_last_month": won_prev_value,
            "lost_or_cancelled": lost(this_month, next_month),
            "lost_or_cancelled_last_month": lost(last_month, this_month),
            "pipeline_value": sum((deal_value(deal) for deal in pipeline), Decimal("0.00")),
            "pipeline_deals": pipeline.count(),
        },
        "upcoming_bids": [
            deal_row(
                deal,
                bid_date=deal.bid_date,
                price_decided=not deal.category_approvals.filter(status__in=undecided).exists(),
            )
            for deal in upcoming[:LIST_SIZE]
        ],
        "upcoming_more": max(len(upcoming) - LIST_SIZE, 0),
        "stuck": [
            deal_row(
                deal,
                reason=f"Waiting for DBGI review for {(now - deal.updated_at).days} days",
            )
            for deal in stuck_reviews[:LIST_SIZE]
        ]
        + [
            deal_row(
                approval.registration,
                reason=(
                    f"{approval.category} price waiting for your approval for "
                    f"{(now - approval.reviewed_at).days} days"
                ),
            )
            for approval in stuck_prices[:LIST_SIZE]
        ],
        "recent_wins": [
            deal_row(
                report.registration,
                won_on=timezone.localtime(report.decided_at).date() if report.decided_at else None,
                value=win_values.get(report.registration_id, Decimal("0.00")),
                certificates_issued=report.certificates_done_at is not None,
            )
            for report in wins
        ],
        "top_partners": [
            {"company_name": name, "deals": count, "value": value}
            for name, (count, value) in top_partners
        ],
        "quarter_label": f"Q{(quarter.month - 1) // 3 + 1} {quarter.year}",
        # Won out of won and lost this quarter; cancelled projects are not counted.
        "win_rate": {
            "won": quarter_won,
            "lost": quarter_lost,
            "percent": (
                round(Decimal(quarter_won) * 100 / (quarter_won + quarter_lost), 1)
                if quarter_won + quarter_lost
                else None
            ),
        },
        "average_discount": {
            "this_month": _average_discount(this_month, next_month),
            "last_month": _average_discount(last_month, this_month),
        },
        "thin_margins": thin[:LIST_SIZE],
        "thin_margins_more": max(len(thin) - LIST_SIZE, 0),
        "thin_margin_percent": THIN_MARGIN_PERCENT,
        "prices_ending": [
            deal_row(
                approval.registration,
                category=approval.category,
                valid_until=approval.valid_until,
                bid_date=approval.registration.bid_date,
            )
            for approval in ending[:LIST_SIZE]
        ],
        "prices_ending_more": max(len(ending) - LIST_SIZE, 0),
    }


def summary_text(overview):
    """The Monday email: the same few numbers, in plain words."""
    month = overview["month"]
    bids = len(overview["upcoming_bids"]) + overview["upcoming_more"]

    def money(value):
        return f"{value:,.2f}"

    lines = [
        f"DBGI portal summary for the week of {overview['today']:%Y-%m-%d}",
        "",
        f"Waiting for your approval: {overview['waiting_for_owner']} price(s).",
        "",
        f"{month['label']} so far:",
        f"- New deals: {month['new_deals']} (last month: {month['new_deals_last_month']})",
        f"- Won: {month['won']}, worth {money(month['won_value'])} "
        f"(last month: {month['won_last_month']}, {money(month['won_value_last_month'])})",
        f"- Lost or cancelled: {month['lost_or_cancelled']} "
        f"(last month: {month['lost_or_cancelled_last_month']})",
        f"- Pipeline: {month['pipeline_deals']} open deal(s), "
        f"worth {money(month['pipeline_value'])}",
        "",
        f"Bids in the next {UPCOMING_DAYS} days: {bids}",
    ]
    for row in overview["upcoming_bids"]:
        note = "" if row["price_decided"] else "  (price not decided yet)"
        lines.append(
            f"- {row['bid_date']:%Y-%m-%d} {row['company_name']}: {row['project_title']}{note}"
        )
    rate = overview["win_rate"]
    discount = overview["average_discount"]
    lines += [
        "",
        f"Win rate, {overview['quarter_label']}: "
        + (
            f"{rate['percent']}% ({rate['won']} won, {rate['lost']} lost)"
            if rate["percent"] is not None
            else "no won or lost projects yet"
        ),
        "Average discount approved: "
        + (f"{discount['this_month']}%" if discount["this_month"] is not None else "none yet")
        + " this month, "
        + (f"{discount['last_month']}%" if discount["last_month"] is not None else "none")
        + " last month",
    ]
    if overview["thin_margins"]:
        lines += [
            "",
            f"Thin margins (less than {overview['thin_margin_percent']}% above landed cost):",
        ]
        lines += [
            f"- {row['company_name']}, {row['product']}: {money(row['approved_price'])} "
            f"(landed cost {money(row['landed_cost'])})"
            for row in overview["thin_margins"]
        ]
    if overview["prices_ending"]:
        lines += ["", f"Prices ending in the next {ENDING_DAYS} days, still bidding:"]
        lines += [
            f"- {row['valid_until']:%Y-%m-%d} {row['company_name']}: {row['category']}"
            for row in overview["prices_ending"]
        ]
    if overview["stuck"]:
        lines += ["", "Stuck:"]
        lines += [
            f"- {row['company_name']}, {row['reference']}: {row['reason']}"
            for row in overview["stuck"]
        ]
    if overview["top_partners"]:
        lines += ["", f"Top partners, {overview['quarter_label']}:"]
        lines += [
            f"- {row['company_name']}: {row['deals']} deal(s), {money(row['value'])}"
            for row in overview["top_partners"]
        ]
    return "\n".join(lines)


def owners():
    from .models import User

    return User.objects.filter(
        Q(is_superuser=True) | Q(is_staff=True, role=User.Role.DBGI_ADMIN),
        is_owner=True,
        is_active=True,
    )
