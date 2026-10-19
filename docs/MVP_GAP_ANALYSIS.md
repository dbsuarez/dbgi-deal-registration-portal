# DBGI Portal MVP Gap Analysis

**Reviewed:** 2026-10-19  
**Source:** `DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md`  
**Current implementation:** Django, Django Ninja, React, MUI, PostgreSQL-ready Docker deployment

## Executive conclusion

The current application is a secure registration-intake foundation, not yet the complete deal-registration workflow described by the specification. Company-scoped submission, editing, evidence attachments, audit events, and administrative maintenance are working. Opportunity matching, ranking, pricing, discount approval, reorders, renewals, notifications, disputes, and reporting are not yet modeled.

The next implementation should establish opportunity matching and the DBGI review lifecycle. Ranking depends on confirmed opportunity or lot membership, so discounts and reorders must not be built before that foundation.

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
- DBGI maintenance through Django Unfold.
- Authentication, CSRF protection, secure session handling, and debug-only accounts.
- Backend, frontend, browser, Docker, migration, and static-asset verification.

## Partial implementations

### Registration status

The database has Submitted, Under review, Approved, and Rejected values. There are no dedicated transition endpoints, required decision reasons, review ownership, changes-requested flow, or transition rules. Status can currently be changed through Django Admin as a general record edit.

### Audit history

Registration submission, company edits, and general admin edits create events. The system does not yet store structured before-and-after differences, matching decisions, rank decisions, withdrawals, disputes, notification delivery, or immutable pricing snapshots.

### Admin review interface

DBGI administrators can see all registrations and use Django Admin. The React interface has no purpose-built review queue, evidence decision controls, matching workspace, ranking view, or decision forms.

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

### P1: Ranking and withdrawal

1. Calculate company-level rank only inside a DBGI-confirmed opportunity or lot scope.
2. Count multiple employees from one company as one company position.
3. Use the original eligible server timestamp, not review time or user-entered dates.
4. Expose only a company's own confirmed rank to company users.
5. Keep provisional and full ranking data DBGI-only.
6. Handle tie and concurrency rules.
7. Support merge and split decisions with reasons and rank impact review.
8. Support company withdrawal requests and DBGI confirmation.

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
7. Add a review page showing registration data, evidence, edit history, and matching controls.
8. Show company users the current review state and actionable change request without exposing other companies.
9. Add permission, transition, concurrency, audit, and tenant-isolation tests.

This slice produces a usable DBGI review loop and creates the data relationships required for ranking. Ranking should be the following slice.

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
