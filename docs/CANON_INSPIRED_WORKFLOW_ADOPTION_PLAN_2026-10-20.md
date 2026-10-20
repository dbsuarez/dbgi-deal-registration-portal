# Canon-Inspired Workflow Adoption Plan

Date: 2026-10-20

## Decision

Use Canon's deal-registration process as a practical business reference, but do not copy its implementation or weaker interaction patterns. The target is Canon's clear separation of business states combined with DBGI's stronger matching, ranking, evidence, audit, concurrency, and security controls.

## Comparison

Canon separates three business questions:

| Business question | Canon model | Current DBGI implementation |
|---|---|---|
| What is happening to the customer project? | Project Status such as Ongoing, Won, or Lost | No dedicated project-status field |
| Where is the registration in the DBGI workflow? | New, Preferred, Supported, Ongoing, Rejected, or Done | Submitted, Under review, Changes requested, Resubmitted, Eligible and matched, Review required, Approved, or Rejected |
| What happened to requested pricing? | Overall price-approval status plus category approvals | Requested prices exist, but there is no implemented pricing-approval workflow |

Canon's separation is clearer operationally. DBGI's implementation is stronger technically in several areas:

- Automatic exact matching with recorded explanations.
- Safe automatic linking when exactly one eligible scope matches.
- Opportunity-scope ranking using original eligible submission time.
- Company isolation and restricted ranking visibility.
- Optimistic concurrency using registration versions.
- Evidence locking once review begins.
- Explicit evidence finalization after attachment changes.
- Verified End-user master data.
- Detailed audit snapshots.
- Attachment validation.
- ISO date presentation.
- No ordinary permanent deletion of business records.

Canon patterns that should not be copied include ambiguous `Save / Submit`, permanent Delete actions in ordinary lists, reuse of `Ongoing` for different concepts, partially successful registration and document submission, inconsistent client validation, ambiguous dates, and generic update history.

## Current implementation gap

The current application is primarily a registration, matching, review, and ranking engine. It is not yet a complete commercial-approval system.

The product catalog has code, name, and category but no authoritative list price. Registration items contain a requested unit price, but the system cannot yet calculate or govern:

- Requested discount percentage.
- Difference from standard price.
- Category price-approval status.
- Approved unit price or discount.
- Approval expiry.
- Renewal eligibility.

## Target model

### Project lifecycle

An opportunity has a separate project status:

- Upcoming
- Active
- Won
- Lost
- Cancelled
- On hold

DBGI administrators control the authoritative status. A later feature may allow company users to report an outcome for confirmation.

### Registration lifecycle

The user-facing registration lifecycle should use plain business language:

- Draft
- Submitted
- Under review
- Changes requested
- Registered
- Rejected
- Closed

Existing precise internal transitions may be retained where required, but `Registered` should be the user-facing meaning of an eligible registration confirmed against an opportunity scope. Registration acceptance must not imply price approval.

### Commercial approval lifecycle

Commercial review is separate from registration review. Each relevant product category receives its own approval record. The category lifecycle is:

- Pending
- Changes requested
- Partially approved
- Approved
- Rejected
- Expired

Approved terms belong to individual product lines so products in the same category can receive different approved prices.

The registration list displays a derived overall price status:

- Not requested
- Pending
- Changes requested
- Partially approved
- Approved
- Rejected
- Expired

The rollup must be deterministic and must not be manually edited.

## Implementation order

### 1. Add project status

- Add the authoritative project status to Opportunity.
- Add transition controls for authorized DBGI administrators.
- Record changes in the registration or opportunity activity history as appropriate.
- Display project status separately from registration status.

### 2. Clarify the visible registration lifecycle

- Preserve safe existing state transitions and stored values where migration risk would otherwise increase.
- Present plain-language labels to users.
- Keep matching state and commercial approval state separate.
- Document each state and available next action through contextual help.

### 3. Add authoritative product pricing

- Add currency and list price to the product catalog.
- Snapshot authoritative list price on submitted registration items.
- Calculate requested discount and line total using decimal arithmetic on the backend.
- Treat requested prices as proposals until commercial approval.

### 4. Add category and line-level price approvals

- Generate one category approval for each distinct catalog product category.
- Store reviewer, rationale, decision timestamp, expiry, and optimistic version.
- Store approved price or approved discount per product line.
- Enforce role permissions, transactions, concurrency, and audit events server-side.

### 5. Upgrade the registration table

Add or expose:

- Reference.
- End-user.
- Project title.
- Company.
- Project status.
- Registration status.
- Price status.
- Total requested value.
- Bid date.
- Age.
- Review indicator.
- Actions.

Company users see only their company records. DBGI administrators see all authorized records and review filters.

### 6. Add expiry and renewal

- Add commercial-approval validity and expiry behavior.
- Show expiring and expired approvals clearly.
- Add renewal requests with reasons and administrator decisions.
- Preserve previous approval terms and expiry history.
- Implement the approved 30-calendar-day renewal rules from the working specification.

## Migration and compatibility approach

- Use additive Django migrations.
- Preserve existing registrations, rankings, events, and opportunity links.
- Backfill safe defaults explicitly.
- Do not silently infer historical approved prices from requested prices.
- Keep all monetary calculations authoritative on the backend.
- Use soft closure or archival rather than ordinary permanent deletion.
- Add tests for transitions, permission boundaries, rollups, calculations, concurrency, tenant isolation, and audit events.

## Product decisions that still require confirmation

- Whether a rejected category makes the overall price result Rejected or Partially approved when another category is approved.
- Whether non-catalog items can receive commercial approval before being added to the product master.
- Who may move a project to Won or Lost and whether company-reported outcomes require confirmation.
- Initial commercial-approval validity before renewals.
- Whether Approved and Registered remain distinct visible terms or Registered replaces the existing Eligible and matched label only.

Until these are confirmed, implementation should use conservative defaults, preserve independent status axes, and avoid irreversible assumptions.
