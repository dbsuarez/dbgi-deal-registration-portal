# DBGI Portal MVP Gap Analysis

**Reviewed:** 2026-10-19  
**Source:** `DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md`  
**Current implementation:** Django, Django Ninja, React, MUI, PostgreSQL-ready Docker deployment

## Executive conclusion

The current application includes the secure registration-intake foundation, opportunity matching and review, strict automatic matching for unambiguous exact matches, and computed company rankings within confirmed opportunity scopes. Pricing, discount approval, withdrawals, merge and split workflows, reorders, renewals, notifications, disputes, and reporting are not yet modeled.

The next implementation should complete ranking exceptions, withdrawals, and opportunity merge or split controls before pricing, discounts, and reorders are added.

## Implemented foundation

- Company and DBGI administrator roles with server-side company scoping.
- Company registration list, detail, create, and edit flows.
- Optimistic concurrency protection through registration versions.
- Required company, end-user, contact, bid, and delivery fields.
- Repeatable competitor items with bid prices and remarks.
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
- DBGI maintenance through Django Unfold.
- Authentication, CSRF protection, secure session handling, and debug-only accounts.
- Backend, frontend, browser, Docker, migration, and static-asset verification.

## Partial implementations

### Registration status

The database and API enforce the initial submitted, review, changes-requested, resubmitted, eligible-and-matched, review-required, and rejected transitions with required reasons and optimistic concurrency. Withdrawal, dispute, merge, split, and pricing approval transitions remain unimplemented.

### Audit history

Registration submission, company edits, general admin edits, review decisions, and automatic matches create events or structured decision records. Rankings are calculated from authoritative scope membership and immutable eligible timestamps rather than stored as editable rank records. Structured field-level differences, withdrawals, disputes, notification delivery, and immutable pricing snapshots remain unimplemented.

### Admin review interface

DBGI administrators can review registration details, inspect explained matching suggestions, record decisions, and view full opportunity rankings in React. More specialized queue filters, merge and split controls, and ranking-impact previews remain unimplemented.

### Product catalog

Products and initial examples exist. Product price versions, VAT basis, scheduled prices, price visibility rules, and historical price selection do not exist.

## Missing capabilities by priority

### P0: Opportunity matching and review foundation

1. Model an internal opportunity separately from company registrations.
2. Represent a procurement lot or ranking scope without relying on similar text fields.
3. Preserve immutable original submission time and original eligibility evidence.
4. Record evidence specificity and credibility review decisions with reviewer, time, and reason.
5. Match a registration to an opportunity or lot through an explicit DBGI decision.
6. Support same-project, partial-lot, and different-project outcomes.
7. Add a controlled registration transition service and API.
8. Add changes-requested and resubmission behavior.
9. Prevent company edits from silently changing reviewed matching or eligibility.
10. Add a DBGI React review queue and review page.

### P1: Remaining ranking and withdrawal work

1. Support merge and split decisions with reasons and rank impact review.
2. Support company withdrawal requests and DBGI confirmation.
3. Add persisted rank-decision snapshots if later pricing approvals require immutable historical rank evidence.

### P2: Price and discount approval

1. Add dated product price versions and future scheduled changes.
2. Add VAT-inclusive or VAT-exclusive basis per maintained price.
3. Add item-level percentage or flat-amount discount approvals.
4. Store approval validity, conditions, approver, reason, and version history.
5. Implement full-precision calculations with line-total rounding to two decimals.
6. Prevent automatic discount stacking.
7. Enforce company price visibility rules in APIs, screens, and exports.
8. Notify the company of approved or changed terms without emailing sensitive detail.

### P3: Reorders, renewals, and exceptions

1. Add multi-line reorder claims linked to approved terms.
2. Show provisional calculations and require DBGI verification.
3. Lock verified reorder snapshots against later price changes.
4. Support pending edits, withdrawals, corrections, reversals, and duplicate review.
5. Handle late or mismatched lines independently.
6. Add clarification requests, deadlines, responses, and overdue queues.
7. Add discount renewal requests and the fixed 30-calendar-day renewal behavior.
8. Preserve line-level processing when other lines remain under review.

### P4: Notifications, reporting, and operations

1. Add durable in-portal notifications and per-event email configuration.
2. Track recipients, attempts, failures, and administrative follow-up.
3. Add role-specific dashboard cards and queue counts.
4. Add authorized reports and exports with company scoping.
5. Finalize attachment scanning, retention, deletion, and backup policies.
6. Add production monitoring, restore drills, and acceptance tests.

## Decisions needed before each phase

### Decide now for P0

- Exact registration review statuses and allowed transitions.
- Whether one opportunity contains explicit child lots or uses ranking scopes that may represent a whole opportunity or a lot.
- Which edits count as material and invalidate a prior review.
- Whether DBGI may return a registration for changes more than once.
- Required reasons for evidence rejection, matching, and status decisions.

## Approved matching assistant

The following matching-assistance behavior was approved on 2026-10-19:

- The application analyzes new and materially edited registrations using transparent business rules.
- It compares normalized end-user names, office and address details, product or SKU overlap, purchase descriptions, dates, evidence, locations, and existing opportunity scopes.
- It recommends one of four outcomes: same opportunity and scope, same opportunity with a new scope, different opportunity, or request clarification.
- Every recommendation displays a confidence level, supporting factors, conflicting factors, and a plain-language explanation through accessible information popovers.
- The DBGI administrator may accept the suggestion, choose another opportunity or scope, create a scope, create a separate opportunity, or request clarification.
- The application automatically links a registration only when exactly one scope has identical normalized end-user and address values, complete requested-product overlap, and no conflicts. All ambiguous, partial, or conflicting matches require a DBGI administrator decision.
- Overrides require an administrator reason.
- Audit history preserves the original suggestion, rule version, factors, confidence, administrator decision, override reason, actor, timestamp, and resulting ranking impact.
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

## Recommended first delivery slice

Build a reviewable vertical slice called **Opportunity Matching and Evidence Review**:

1. Add `Opportunity` and `OpportunityScope` models.
2. Add structured review state and immutable original-submission fields to `Registration`.
3. Add a review-decision model containing decision type, rationale, actor, and timestamp.
4. Add transactional services for start review, request changes, resubmit, match, reject, and confirm eligibility.
5. Add DBGI-only APIs with explicit input and output schemas.
6. Add a DBGI review queue with search, filters, pagination, and review-needed indicators.
7. Add a review page showing registration data, evidence, edit history, matching suggestions, accessible explanations, and confirmation controls.
8. Show company users the current review state and actionable change request without exposing other companies.
9. Add permission, transition, concurrency, audit, and tenant-isolation tests.

This review slice and the initial read-only opportunity ranking slice are implemented. Rankings are computed from confirmed scope membership and original eligible timestamps.

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
