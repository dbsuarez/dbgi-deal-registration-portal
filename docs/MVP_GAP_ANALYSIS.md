# DBGI Portal MVP Gap Analysis

**Reviewed:** 2026-10-21

**Source:** `DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md`

**Current implementation:** Django, Django Ninja, React, MUI, PostgreSQL-ready Docker deployment

## Executive conclusion

The current application includes secure registration intake, governed master data, opportunity matching and review, strict automatic matching for unambiguous exact matches, computed company rankings, project status, and an initial category and item commercial-approval workflow with expiry and 30-day renewals. Withdrawal, merge and split workflows, authoritative dated prices, complete discount calculation, reorders, notifications, disputes, and reporting are not yet modeled.

The next implementation should close lifecycle-policy gaps, withdrawals, and opportunity merge or split controls before authoritative pricing and reorder work expands.

## Implemented foundation

- Company and DBGI administrator roles with server-side company scoping.
- Company registration list, detail, create, and edit flows.
- Optimistic concurrency protection through registration versions.
- Required company, end-user, contact, bid, and delivery fields.
- Repeatable competitor items with bid prices and remarks.
- Managed competitor brands with aliases and canonical resolution.
- Governed End-user directory with company proposals and DBGI verification.
- Repeatable requested products with catalog and non-catalog choices.
- Requested quantity, unit price, and justification.
- Evidence description, public link, sharing confirmation, and private attachments.
- Attachment extension and size validation plus permission-scoped downloads.
- Submission and edit audit events with snapshots.
- Material edits marked for DBGI review.
- Versioned, explainable opportunity-matching suggestions.
- Strict automatic matching when one scope has exact normalized end-user and address values, complete product overlap, and no conflicts.
- DBGI review decisions for ambiguous or partial matches.
- Company-level ranking by immutable original eligible timestamp.
- DBGI full-ranking visibility and company-scoped own-rank visibility.
- Shared rank display for exact timestamp ties.
- Separate project, registration, and commercial-approval status axes.
- Category commercial approvals, item-level approved prices, expiry, and 30-day renewals.
- PostgreSQL concurrency coverage for registration edits, evidence finalization, matching refresh, and normalized master-data uniqueness.
- Shared request throttling and explicit DBGI administration authorization.
- GitHub Actions gates for backend, PostgreSQL, frontend, build, and browser checks.
- DBGI maintenance through Django Unfold.
- Authentication, CSRF protection, secure session handling, and debug-only accounts.
- Backend, frontend, browser, Docker, migration, and static-asset verification.

## Partial implementations

### Registration status

The database and API enforce the initial submitted, review, changes-requested, resubmitted, eligible-and-matched, review-required, and rejected transitions with required reasons and optimistic concurrency. Withdrawal, dispute, merge, and split transitions remain unimplemented. Commercial approval is tracked separately from registration eligibility.

### Audit history

Registration submission, company edits, general admin edits, review decisions, automatic matches, evidence changes, project-status changes, commercial decisions, and renewals create events or structured decision records. Admin registration and child-inline edits preserve immutable before and resulting snapshots. Rankings are calculated from authoritative scope membership and immutable eligible timestamps rather than stored as editable rank records. Structured field-level differences, withdrawals, disputes, notification delivery, and authoritative dated pricing snapshots remain unimplemented.

### Admin review interface

DBGI administrators can review registration details, inspect explained matching suggestions, record decisions, and view full opportunity rankings in React. More specialized queue filters, merge and split controls, and ranking-impact previews remain unimplemented.

### Product catalog

Products and initial examples exist. Product price versions, VAT basis, scheduled prices, price visibility rules, and historical price selection do not exist.

### Commercial approvals

Category approvals, item-level approved prices, validity dates, expiry behavior, mixed status rollups, and 30-day renewal decisions exist. Percentage or flat-amount discount models, authoritative dated product prices, VAT basis, complete rounding policy, scheduled prices, and historical price-version selection remain unimplemented.

## Missing capabilities by priority

### P0: Lifecycle and ranking exceptions

1. Support company withdrawal requests and DBGI confirmation.
2. Support merge and split decisions with reasons and rank-impact previews.
3. Define and implement advance-registration expiry, clarification holds, and extensions.
4. Add disputes without silently suspending existing decisions.
5. Add persisted rank-decision snapshots if later pricing approvals require immutable historical rank evidence.

### P1: Complete price and discount authority

1. Add dated product price versions and future scheduled changes.
2. Add VAT-inclusive or VAT-exclusive basis per maintained price.
3. Extend item-level approved prices with percentage or flat-amount discount approvals.
4. Preserve full commercial version history and conditions.
5. Implement full-precision calculations with line-total rounding to two decimals.
6. Prevent automatic discount stacking.
7. Enforce company price visibility rules in APIs, screens, and exports.
8. Notify the company of approved or changed terms without emailing sensitive detail.

### P2: Reorders and exceptions

1. Add multi-line reorder claims linked to approved terms.
2. Show provisional calculations and require DBGI verification.
3. Lock verified reorder snapshots against later price changes.
4. Support pending edits, withdrawals, corrections, reversals, and duplicate review.
5. Handle late or mismatched lines independently.
6. Add clarification requests, deadlines, responses, and overdue queues.
7. Preserve line-level processing when other lines remain under review.

### P3: Notifications, reporting, and operations

1. Add durable in-portal notifications and per-event email configuration.
2. Track recipients, attempts, failures, and administrative follow-up.
3. Add role-specific dashboard cards and queue counts.
4. Add authorized reports and exports with company scoping.
5. Finalize attachment scanning, retention, deletion, and backup policies.
6. Add production monitoring, restore drills, and acceptance tests.

## Decisions needed before each phase

### Decide now for lifecycle work

- Exact registration review statuses and allowed transitions.
- Whether one opportunity contains explicit child lots or uses ranking scopes that may represent a whole opportunity or a lot.
- Which edits count as material and invalidate a prior review.
- Whether DBGI may return a registration for changes more than once.
- Required reasons for evidence rejection, matching, and status decisions.

## Approved matching assistant

The following matching-assistance behavior was approved on 2026-10-19:

- The application analyzes new and materially edited registrations using transparent business rules.
- The current rule version compares normalized End-user names, normalized addresses, catalog-product overlap, and existing opportunity scopes. Dates, evidence quality, location detail beyond the stored address, and purchase-description similarity remain possible future factors and must not be represented as current scoring inputs.
- It recommends one of four outcomes: same opportunity and scope, same opportunity with a new scope, different opportunity, or request clarification.
- Every recommendation displays a confidence level, supporting factors, conflicting factors, and a plain-language explanation through accessible information popovers.
- The DBGI administrator may accept the suggestion, choose another opportunity or scope, create a scope, create a separate opportunity, or request clarification.
- The application automatically links a registration only when exactly one scope has identical normalized end-user and address values, complete requested-product overlap, and no conflicts. All ambiguous, partial, or conflicting matches require a DBGI administrator decision.
- Overrides require an administrator reason.
- Audit history preserves the suggestion, rule version, factors, confidence, administrator decision, rationale, actor, and timestamp. A persisted resulting ranking-impact snapshot remains future work.
- Matching details about other companies remain DBGI-only. Company users see only their own confirmed outcome and clarification requests.

Start with deterministic, versioned rules. Machine-learning or external AI matching may be evaluated later only if it preserves explainability, authorization boundaries, and administrator control.

### Defer until pricing work

- Initial discount validity duration.
- VAT breakdown and rounding mode.
- Price visibility details beyond approved products.
- Reminder lead times and Philippine business-day rules.

### Defer until operations work

- Email provider and recipient configuration.
- Final file scanning and retention policy.
- Export catalog and report layouts.
- Production backup retention and restore targets.

## Completed first delivery slice

The reviewable vertical slice called **Opportunity Matching and Evidence Review** is implemented:

1. Add `Opportunity` and `OpportunityScope` models.
2. Add structured review state and immutable original-submission fields to `Registration`.
3. Add a review-decision model containing decision type, rationale, actor, and timestamp.
4. Add transactional services for start review, request changes, resubmit, match, reject, and confirm eligibility.
5. Add DBGI-only APIs with explicit input and output schemas.
6. Add a DBGI review queue with search, filters, pagination, and review-needed indicators.
7. Add a review page showing registration data, evidence, edit history, matching suggestions, accessible explanations, and confirmation controls.
8. Show company users the current review state and actionable change request without exposing other companies.
9. Add permission, transition, concurrency, audit, and tenant-isolation tests.

Rankings are computed from confirmed scope membership and original eligible timestamps. Remaining lifecycle and commercial work is tracked in `PRODUCT_ROADMAP_2026-10-21.md`.

## Approved initial registration lifecycle

The following initial lifecycle was approved on 2026-10-19:

```text
Submitted -> Under review
Under review -> Changes requested
Changes requested -> Resubmitted
Resubmitted -> Under review
Under review -> Eligible and matched
Under review -> Rejected
Eligible and matched -> Review required after material edit
Review required after material edit -> Under review
```

Approval of a commercial discount should remain separate from registration eligibility and matching.
