# DBGI Project Registration Portal: Current Capabilities

**As of:** 2026-10-30  
**Status:** Working internal beta, not yet production-ready  
**Source:** Current baseline in [PRODUCT_ROADMAP_2026-10-21.md](PRODUCT_ROADMAP_2026-10-21.md)

The portal covers the core loop end to end: a partner company registers a deal, DBGI matches and ranks it, and DBGI approves pricing, with notifications throughout.

## Company users (partner dealers)

- **Register deals:** create and edit registrations for specific procurement opportunities. Contact details are prefilled from the user's profile, and concurrent edits cannot silently overwrite each other.
- **End-users:** choose an End-user from a DBGI-governed directory, or propose a new one. The add form has Region, Province, and City/Municipality selectors, controlled classification lists, and field help.
- **Competitors:** record competitor items with brand and model suggestions. Canon, Epson, HP, and Lexmark are seeded, and brand aliases resolve (for example, Hewlett Packard resolves to HP).
- **Products and pricing:** request catalog or non-catalog products with quantity and requested price. The list price is captured at request time, and the discount and totals are calculated.
- **Evidence:** upload private evidence files, which are validated, finalized, locked, and audited.
- **Tracking:** a registration list with search, quick and advanced filters, and pagination. Status badges explain themselves on hover or keyboard focus, and ranking views show only what the company is allowed to see.
- **Report the project outcome:** once DBGI links a registration to a project, report it as Won, Lost, or Cancelled with a short note. DBGI confirms or declines it.
- **Withdraw:** withdraw a registration with a short reason. Withdrawal is final: the registration leaves the ranking and can no longer change, and DBGI is notified.
- **Notifications and help:** in-portal notifications for everyone in the company, with email only to the person who submitted, and a Help page with step-by-step beginner walkthroughs.

## DBGI administrators

- **Matching:** the system suggests matches and auto-matches only when it is safe to. Administrators review step by step and can open a dialog explaining each match. Matched registrations are grouped into opportunity scopes, and companies are ranked within each.
- **60-day limits:** registrations not confirmed within 60 days, and registrations on projects on hold for 60 days, come back to the review queue; companies get a reminder 7 days before. This runs through a daily job that must be scheduled on the server.
- **Outcome reports:** confirm or decline a company's Won, Lost, or Cancelled report from the registration page; confirming sets the project status for every linked registration.
- **Commercial approvals:** approve pricing by product category with item-level approved prices, an expiry date, and 30-day renewals. Project status, registration status, and pricing approval are tracked separately.
- **End-user verification:** review company-proposed End-users and maintain the Organization type and Sector lists.
- **Operations dashboard (Django Admin):** work queues for pending review, pricing, End-user verification, failed emails, and approvals nearing expiry.
- **Notifications:** per-event email templates with previews, delivery tracking, and retries. Email is sent from the DBGI support mailbox over MXroute.
- **Audit:** activity history with field-level change summaries, and before-and-after snapshots of edits made in Django Admin.
- **Superuser tools:** a Danger Zone that bulk-deletes transactional data while keeping users and reference data, and a debug-only Scenario Lab for setting up test cases.

## Platform and safeguards

- Each company sees only its own data, enforced on the server.
- Login and data changes are rate-limited across workers, and Django Admin access is explicitly permission-checked.
- Concurrency is safe on PostgreSQL, with dedicated tests.
- GitHub Actions runs backend, PostgreSQL, frontend, build, formatting, and browser tests.
- In debug mode, a test-data panel offers presets shared between developers. All debug tools are disabled in production.

## Not yet available

| Capability                                          | Roadmap milestone | Waiting on                         |
| --------------------------------------------------- | ----------------- | ---------------------------------- |
| Opportunity merge and split                         | 1                 | Product-owner merge and split rule |
| Versioned price history and full renewal processing | 2                 | Finance and pricing decisions      |
| Reorder verification                                | 3                 | Milestone 2                        |
| Role-specific dashboard counts and exports          | 4                 | None (can start now)               |
| Production deployment, monitoring, and backups      | 5                 | Earlier milestones                 |

See the roadmap's decision register (section 12) for the open policy decisions and their owners.
