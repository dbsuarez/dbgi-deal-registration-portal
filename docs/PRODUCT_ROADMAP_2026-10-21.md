# DBGI Project Registration Portal Roadmap

**Prepared:** 2026-10-21  
**Status:** Working delivery roadmap  
**Source documents:** Working Design Specification v9, MVP Gap Analysis, Canon research and adoption plan, audit handoff, repository history, and current implementation

## 1. Product objective

Deliver a secure DBGI portal where partner companies register specific procurement opportunities, DBGI confirms matching and rank, commercial terms are approved separately, and later qualifying orders are verified against those terms.

The portal is a commercial deal-registration system. It does not determine government bid awards, expose competitors' data to partner companies, or treat a requested price as an approved price.

## 2. Current baseline

The application is a working internal beta with these foundations implemented:

- Django, Django Ninja, React, TypeScript, MUI, Django Unfold, and Docker architecture.
- Company and DBGI administrator roles with server-side company scoping.
- Debug-only development accounts and scenario controls that fail closed outside debug mode.
- Registration list, detail, create, and edit flows with optimistic concurrency.
- Governed End-user directory with company proposals and DBGI verification.
- Repeatable competitor items and managed competitor-brand master data with aliases.
- Canon, Epson, HP, and Lexmark seed brands, with Hewlett Packard resolving to HP.
- Catalog and non-catalog requested products, quantity, list-price snapshot, requested price, discount calculation, and requested totals.
- Private evidence attachments, content validation, staged upload finalization, locking, and audit events.
- Deterministic matching suggestions, strict safe auto-match, administrator review decisions, opportunity scopes, and company-level rankings.
- Separate project, registration, and commercial-approval status axes.
- Category commercial approvals, item-level approved prices, expiry, and 30-day renewal decisions.
- Project-status management and activity history.
- Table search, filters, pagination, status indicators, and permission-scoped ranking views.
- Structured frontend API errors that preserve backend codes and field details.
- An application-level not-found page with a safe return action.
- Shared Redis-backed throttling for login submissions and authenticated API mutations across Gunicorn workers.
- Constant-query matching product overlap and composite indexes for company lists and eligible-scope rankings.
- Explicit Django Admin authorization through a DBGI-specific admin site permission gate.
- Immutable before-and-resulting snapshots for Django Admin registration and child-inline edits.
- PostgreSQL-safe row locking and concurrency coverage for simultaneous edits, evidence finalization, matching refresh, and normalized End-user uniqueness.
- GitHub Actions quality gates for backend, PostgreSQL, frontend, build, formatting, and Playwright checks.
- Browser accessibility coverage for dialog naming, keyboard activation, initial focus, Escape dismissal, focus restoration, and API error alerts.
- Development runbook guidance to apply pending migrations after pulling application changes.
- Project-scoped MemPalace retrieval for the reviewed documentation and tracked application source, using the lightweight MCP server without automatic transcript or whole-repository mining.
- A curated MemPalace conversation-continuity entry covering the available project history, operating rules, completed competitor-brand work, local setup, and known limitations.
- Shared MemPalace access for Claude Code through a git-ignored, project-scoped MCP registration, with per-agent diaries for Claude and Codex handoffs.
- Durable, recipient-scoped portal and email notifications for submissions, registration decisions, and category price decisions, with read tracking, delivery tracking, administrator retries, per-event subject and body templates, rendered administrator previews, immutable delivery-content snapshots, and a dedicated post-submission Help page.
- Environment-backed MXroute SMTP delivery using the DBGI support mailbox, with credentials excluded from tracked source.
- Compact registration activity history with small action rows and collapsed-by-default structured field changes.
- Role-aware Help page with beginner company walkthroughs, administrator operating procedures, status explanations, direct task links, and troubleshooting guidance.
- Role-specific end-to-end practice scenarios with prerequisites, exact actions, and expected outcomes for registration, correction, matching, pricing, notification recovery, and governed End-user workflows.
- Django Admin operations dashboard with actionable review, pricing, End-user verification, failed-email, and expiring-approval queues.
- Beginner-friendly, role-aware Help instructions that users can follow one step at a time, with options to open Help in the current page, a new tab, or a distraction-free side-by-side window.
- Local checks covering Django, Ruff, Vitest, Playwright, TypeScript builds, migrations, and deployment configuration.

The application is not yet production-ready. Withdrawal, opportunity merge and split, authoritative price versioning, complete reorder processing, reporting, operational automation, and several policies remain incomplete.

## 3. Delivery principles

- Keep project status, registration review, rank, and commercial approval independent.
- Enforce authorization, validation, calculations, and transitions on the backend.
- Preserve original eligible timestamps and immutable decision evidence.
- Keep competitor information, evidence, detailed pricing, and full rankings appropriately restricted.
- Prefer archival, cancellation, or reversal over permanent deletion of business records.
- Use additive migrations and preserve historical snapshots.
- Do not infer unresolved pricing, tax, retention, or procurement policy.
- Require PostgreSQL verification for behavior that depends on row locking.
- Treat each milestone as complete only after permissions, concurrency, migration, UI, and regression checks pass.

## 4. Roadmap overview

| Milestone                                     | Outcome                                                     | Priority       | Depends on                    |
| --------------------------------------------- | ----------------------------------------------------------- | -------------- | ----------------------------- |
| 0. Stabilize the internal beta                | Known technical and test risks are closed                   | P0             | Current codebase              |
| 1. Close workflow policy and lifecycle gaps   | Withdrawal, merge, split, and clear status rules are usable | P0             | Product-owner decisions       |
| 2. Complete commercial pricing                | Prices and approvals are historically authoritative         | P1             | Finance and pricing decisions |
| 3. Deliver reorder verification               | Approved terms can support controlled repeat orders         | P1             | Milestone 2                   |
| 4. Add notifications, dashboards, and reports | Work is visible, actionable, and auditable                  | P2             | Stable workflows              |
| 5. Production readiness and launch            | The portal can safely operate at registration.dbgi.ph       | P0 launch gate | All launch-scope milestones   |

## 5. Milestone 0: Stabilize the internal beta

### Scope

1. Resolve remaining audit items:
   - [x] Add throttling for login and sensitive endpoints.
   - [x] Preserve structured API error codes and field details in the frontend.
   - [x] Review missing indexes and remove the matching-loop N+1 query.
   - [x] Add a safe application-level not-found route.
   - [x] Replace broad admin URL-prefix assumptions with explicit authorization.
   - [x] Verify that Django Admin child-inline edits capture complete before-and-after audit evidence.
2. [x] Add PostgreSQL integration tests for row locks, concurrent registration edits, matching refresh, evidence finalization, and duplicate normalized master data.
3. [x] Add CI quality gates for backend tests, frontend tests, Ruff, migration drift, build, and representative Playwright workflows.
4. [x] Reconcile stale documentation, especially the README current-scope section and the old MVP gap analysis.
5. [x] Add focused accessibility coverage for dialogs, keyboard navigation, focus restoration, and error states.
6. [x] Prepare the separate technical and infrastructure proposal required by v9 before production implementation.

### Exit criteria

- Full backend, frontend, and browser suites pass in CI.
- PostgreSQL concurrency tests demonstrate the intended locking behavior.
- No high-severity audit item remains open.
- Current-scope documentation matches the implemented models and APIs.

## 6. Milestone 1: Close workflow policy and lifecycle gaps

### Product decisions required first

- Final user-facing registration labels and allowed transitions.
- Whether submitted registrations remain editable or require a returned-for-changes state.
- Exact authority for setting Won, Lost, Cancelled, and On hold.
- Withdrawal request, confirmation, restoration, and ranking-removal rules.
- Opportunity and scope merge or split rules, including rank and commercial-term impact.
- Treatment of ties and any required immutable rank-decision snapshot.
- Advance-registration expiry, reminder, clarification-period, extension, and sufficiently-specific-evidence rules.
- Detailed postponed, failed, cancelled, and reposted government-notice policy.

### Engineering scope

1. Add company withdrawal requests with reason and DBGI confirmation.
2. Add administrator merge and split workflows with impact previews and mandatory rationale.
3. Recalculate or preserve affected ranks according to the approved policy.
4. [x] Add field-level change summaries for material edits and administrator decisions.
5. Improve the DBGI review queue with saved filters for matching, edited records, withdrawals, and merge or split review.
6. Add contextual help that clearly distinguishes project, registration, ranking, and pricing states.
7. Add configurable advance-registration expiry, reminders, clarification holds, and reasoned pre-expiry extensions.
8. Preserve original priority during a clarification hold only when the original claim was sufficiently specific.
9. Add company-requested disputes for rejection, matching, rank, withdrawal, discount, renewal, and reorder decisions without silently suspending the existing decision.

### Exit criteria

- Every lifecycle transition has an actor, timestamp, reason, permission rule, and test.
- Companies cannot see another company's registration, competitor data, evidence, or ranking details.
- Merge, split, and withdrawal operations preserve history and never silently rewrite original eligibility.

## 7. Milestone 2: Complete commercial pricing

### Product decisions required first

- Initial approval-validity duration and reminder lead time.
- VAT-inclusive and VAT-exclusive treatment.
- PHP rounding mode and multi-line reconciliation policy.
- Effective-time and time-zone rules for price changes.
- Whether non-catalog products can be approved before catalog onboarding.
- Overall status behavior when categories have mixed approval results.
- Company price-visibility rules for current prices, approved products, APIs, and exports.

### Engineering scope

1. Replace a single mutable product list price with dated, versioned prices.
2. Record currency, VAT basis, effective start, optional end, creator, and change reason.
3. Select and snapshot the authoritative price version during registration and later order verification.
4. Complete item-level approved-price and discount calculations using backend decimal arithmetic.
   - Support either a percentage discount or a flat peso amount per unit.
   - Calculate percentage line totals from full precision and round the line total to two decimals.
   - Show no discount figures to company users before DBGI approval.
5. Add approval-expiry processing, expiring-term queues, and renewal visibility.
6. Complete company and administrator renewal workflows, including before-expiry and after-expiry behavior.
   - Each approved renewal adds 30 calendar days.
   - Approval before expiry extends the existing expiry; approval after expiry starts from the approval date and does not cover the gap.
   - Warn users to allow at least one working day for review without presenting it as a guarantee.
7. Add explicit rules preventing automatic discount stacking.
8. Display `Subject to availability` without inventing inventory quantities or implying stock reservation.
9. Add commercial decision history and reports without exposing sensitive pricing to unauthorized companies.

### Exit criteria

- Historical approvals never change when catalog prices change.
- Requested, list, approved, and expired prices are visually and semantically distinct.
- Calculation and rounding examples are approved by DBGI's finance or pricing owner.
- Mixed-category status rollups are deterministic and tested.

## 8. Milestone 3: Deliver reorder verification

### Scope

1. Add reorder headers and multiple product lines under one purchase reference.
   - One active approval may cover multiple qualifying reorders for the same company, End-user, and product, with no aggregate quantity or value cap before expiry.
   - A new procurement notice does not automatically cancel an existing eligible discount, but the previous registration rank does not transfer to the new opportunity.
2. Let company users create, edit, and withdraw pending lines with reasons.
3. Calculate provisional prices only when company, End-user, product, date, and active approval match.
   - Use the required provisional label explaining that DBGI verification and stock availability still apply.
4. Require DBGI verification before terms become final.
   - Ordinary reorder proof is not mandatory, but DBGI may require it for an exception.
5. Snapshot the verified order date, price version, approval version, unit price, discount, totals, and verifier.
6. Lock verified lines and support reasoned correction or reversal without replacing the original snapshot.
7. Add late, expired, mismatched, and clarification-required flows.
8. Add duplicate detection as a review flag, never an automatic merge or rejection.
9. Support independent line outcomes so one exception does not block valid lines.
10. Support company-only wait-for-discount drafts for expired terms.
    - Permit submission at regular price as the alternative, and do not apply a later discount retroactively.
    - Retain an audit event when a waiting draft is deleted.
11. Add post-verification reduction, cancellation, and return requests.
    - Put the affected verified line on hold for DBGI review without changing its original snapshot.
    - Support separate decisions for an unshipped cancellation and a shipped-product return in the same case.

### Exit criteria

- Verified records remain unchanged by later product-price or approval changes.
- Duplicate, late, and mismatched claims require explicit review.
- Every line has a clear state, permitted next action, and audit history.
- A company cannot directly edit or withdraw a verified line and must request a correction.
- Cross-company access tests cover APIs, files, exports, and direct identifiers.

## 9. Milestone 4: Notifications, dashboards, and reports

### Scope

1. [x] Add durable in-portal notifications as the authoritative channel.
2. [x] Add per-event portal-only or portal-plus-email configuration.
3. [x] Track recipients, attempts, failures, retries, and administrator follow-up.
4. [x] Exclude competitor details, private evidence, and detailed sensitive pricing from email.
5. Add role-specific dashboard counts and actionable review queues.
6. Add authorized CSV or Excel exports for registrations, project pipeline, approvals, renewals, reorders, exceptions, and audit activity.
7. Preserve active filters and make export scope explicit.
8. Include durable queues for pending renewals, nearing-expiry terms, reorder verification, exception clarification, overdue responses, withdrawals, disputes, and material edits.

### Exit criteria

- Failed email never removes or completes the corresponding portal task.
- Company reports contain only that company's authorized data.
- DBGI reports identify source filters, generation time, and actor.

## 10. Milestone 5: Production readiness and launch

### Infrastructure and security

1. Provision the production PostgreSQL database and private attachment storage.
2. Configure Cloudflare, Nginx, HTTPS, allowed hosts, CSRF origins, secure cookies, proxy headers, and reviewed HSTS settings.
3. Keep Django and PostgreSQL ports private.
4. Add rate limiting, Sentry, uptime monitoring, structured logs, and alert ownership.
5. Define attachment scanning, retention, deletion, and incident-response procedures.
6. Automate encrypted database and media backups and complete a restore drill.
7. Define secret rotation, dependency updates, and administrator-access review.

### Acceptance and rollout

1. Run production-like migration, security, performance, and permission tests.
2. Execute the specification's company-isolation, matching, ranking, pricing, renewal, and reorder acceptance scenarios.
3. Conduct role-based user acceptance testing with DBGI administrators and representative company users.
4. Load approved production companies, users, products, prices, and settings without development accounts or sample transactions.
5. Use a controlled pilot, document support ownership, and define rollback criteria before general availability.

### Launch gate

- `DEBUG=False` and deployment checks pass.
- Backup restore is demonstrated.
- No critical or high security finding remains open.
- Product owners approve workflow and pricing policies.
- Monitoring, alerting, and operational owners are active.

## 11. Recommended next delivery slice

Start with **Internal Beta Stabilization and Workflow Closure**:

1. Update stale scope documentation.
2. Close the remaining audit items and add PostgreSQL concurrency coverage.
3. Confirm registration labels, editing rules, withdrawal policy, and merge or split policy.
4. Implement withdrawal requests and DBGI confirmation.
5. Add merge and split impact previews only after the policy is approved.

This slice reduces technical risk before the portal accumulates price history and reorder records that are harder to correct later.

## 12. Decision register for the next product meeting

| Decision                                                 | Needed by   | Owner                         |
| -------------------------------------------------------- | ----------- | ----------------------------- |
| Final registration labels and transitions                | Milestone 1 | DBGI product owner            |
| Submitted-record editing rule                            | Milestone 1 | DBGI product owner            |
| Withdrawal and restoration policy                        | Milestone 1 | DBGI product owner            |
| Opportunity merge and split effects                      | Milestone 1 | DBGI product owner            |
| Initial commercial validity                              | Milestone 2 | DBGI commercial owner         |
| VAT and rounding policy                                  | Milestone 2 | DBGI finance or pricing owner |
| Non-catalog approval rule                                | Milestone 2 | DBGI commercial owner         |
| Reorder evidence and duplicate-review policy             | Milestone 3 | DBGI operations owner         |
| Postponed, failed, cancelled, and reposted notice policy | Milestone 1 | DBGI product owner            |
| Notification recipients and email provider               | Milestone 4 | DBGI operations and IT        |
| Retention, backup targets, and restore objectives        | Milestone 5 | DBGI IT and management        |

## 13. Deferred work

- Machine-learning matching. Keep deterministic, explainable rules until the workflow and training evidence are mature.
- Inventory reservation or guaranteed availability without an authoritative inventory integration.
- Automatic government-award conclusions.
- Automatic merging or rejection of possible duplicate reorders.
- Any integration with Odoo unless separately approved and designed.

## 14. Roadmap maintenance

Update this document after each milestone or product-policy decision. Move completed items into the current baseline, record the approving decision and date, and keep unresolved policy separate from engineering tasks. Do not mark a milestone complete based only on UI availability; its backend permissions, migrations, audit behavior, and verification gates must also be complete.
