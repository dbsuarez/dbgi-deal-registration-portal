# DBGI Project Registration Portal Technical and Infrastructure Proposal

**Prepared:** 2026-10-21

**Status:** Proposed for DBGI technical, security, operations, and product-owner approval

**Source:** `DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md`

## 1. Executive recommendation

Deploy the portal as a Docker Compose application on a dedicated Hostinger VPS. Cloudflare terminates public HTTPS traffic and forwards only approved web traffic to Nginx. Nginx serves the compiled React application and proxies authenticated operations to Django and Django Ninja. PostgreSQL and Redis remain on a private Docker network and expose no public host ports.

Treat the current application as an internal beta until the launch gates in this proposal pass. Production approval requires DBGI decisions for lifecycle, pricing, attachments, retention, notification recipients, recovery objectives, and operational ownership.

## 2. Architecture decision

### Proposed production topology

```text
Browser
  -> Cloudflare HTTPS, DNS, and edge controls
    -> VPS firewall, ports 80 and 443 only
      -> Nginx container
        -> React static assets
        -> Django and Django Ninja web container
          -> PostgreSQL container on private network
          -> Redis container on private network
          -> Private attachment storage
```

Run at least three Gunicorn workers initially. Use Redis for shared request throttling across workers. Keep PostgreSQL data, attachment storage, and backup material outside application images.

### Recorded frontend divergence

The v9 specification initially preferred Django templates with progressive enhancement. The implemented internal beta uses a separate React, TypeScript, and MUI frontend while retaining Django-controlled authentication, authorization, validation, transactions, and data access. DBGI should explicitly approve this divergence before production. The security boundary remains the Django backend; frontend visibility never grants permission.

### Deferred components

- Add background workers only when durable notification delivery, scheduled expiry processing, file scanning, or report generation requires them.
- Prefer private S3-compatible object storage before production attachment volume grows. A private Docker media volume is acceptable only for a controlled pilot with encrypted off-host backup and a completed restore drill.
- Do not add machine-learning matching until deterministic rules and evidence are mature.

## 3. Environments and release flow

Maintain separate local, test, staging, and production configurations.

| Environment | Data | Purpose | Required controls |
| --- | --- | --- | --- |
| Local | Generated development data only | Developer work | `DEBUG=True`, local-only accounts |
| CI | Disposable SQLite and PostgreSQL databases | Automated verification | No production secrets or data |
| Staging | Sanitized or synthetic data | Migration, integration, and acceptance testing | Production-like security settings |
| Production | Approved business data | Live service | `DEBUG=False`, reviewed secrets, monitoring, backups |

Release from a reviewed Git commit. CI must pass backend tests on SQLite and PostgreSQL, Ruff, migration drift, frontend formatting, lint, component tests, build, and Playwright workflows. Apply migrations as an explicit release step before switching traffic. Define rollback criteria for application images and a forward-fix or restore plan for each schema migration.

## 4. Pages and access boundaries

### Company users

- Registration list, search, filters, and authorized ranking view.
- Registration create, detail, permitted edit, and evidence management.
- End-user proposal when verified master data is unavailable.
- Future withdrawal, dispute, renewal, reorder, notification, and report pages only after their policies are approved.

Company access is always scoped by authenticated company membership. A company must never retrieve another company's registration, evidence, competitor details, requested pricing, approvals, or full ranking data by changing a URL or identifier.

### DBGI administrators

- React review queue, registration detail, matching explanations, review decisions, project status, and complete rankings.
- Django Admin for users, companies, End-users, competitor brands, products, opportunities, commercial approvals, audit history, and controlled development scenarios.
- Future merge, split, withdrawal, pricing history, notification, reorder, exception, and reporting controls.

Django Admin access requires an active staff user with the DBGI administrator role or a superuser. Model permissions still control individual administration sections.

## 5. Data and transaction design

PostgreSQL is the authoritative datastore. Preserve relational links among companies, users, End-users, registrations, requested products, evidence, opportunities, scopes, suggestions, decisions, rankings, commercial approvals, renewals, events, and future reorder records.

Apply these rules:

- Keep project status, registration review, rank, and commercial approval as separate axes.
- Preserve original submission and eligible timestamps.
- Use optimistic versions for user-visible edit conflicts and PostgreSQL row locks for critical transitions.
- Keep normalized uniqueness constraints for governed master data.
- Store immutable before and resulting audit snapshots for sensitive administration edits.
- Add dated product-price and commercial versions before authoritative pricing or reorder verification.
- Archive or reverse business records instead of silently deleting history.
- Use additive migrations and review data backfills separately from schema changes when practical.

Ranking remains derived from confirmed scope membership and original eligible timestamps. Merge, split, withdrawal, ties, and persisted rank-impact snapshots require approved policy before implementation.

## 6. Security and privacy controls

- Keep Django, PostgreSQL, and Redis ports private.
- Store secrets only in protected environment or secret-management facilities, never in Git or container images.
- Configure allowed hosts, trusted CSRF origins, secure cookies, proxy SSL headers, content-type protections, and reviewed HSTS settings.
- Restrict Cloudflare origin access and the VPS firewall to required traffic.
- Use backend object-level authorization for every API and file download.
- Retain shared throttling for login submissions and authenticated API mutations. Review limits from production traffic and security evidence.
- Log actor, action, target, outcome, and timestamp without logging credentials, session tokens, private evidence content, or unnecessary personal data.
- Review administrator access regularly and define joiner, mover, leaver, and emergency-access procedures.
- Complete dependency, vulnerability, and container-image review before launch.

## 7. Attachments and evidence

Current prototype limits are not final policy: 10 MiB per file and PDF, PNG, JPG, JPEG, DOCX, and XLSX formats. Before production, DBGI must approve permitted content, retention, deletion, legal hold, malware scanning, and incident handling.

Required controls:

- Random storage names and original-name metadata.
- Authenticated, company-scoped or DBGI-authorized downloads.
- No direct public media serving.
- Content-signature validation in addition to extensions.
- Malware scanning before a file becomes available to reviewers.
- Encryption in transit and at rest.
- Database and attachment backups coordinated to a recoverable point.
- Tested deletion and restore procedures that preserve audit requirements.

## 8. Notifications and background work

Use durable in-portal notifications as the authoritative channel. Email is optional delivery assistance and must not contain competitor details, private evidence, or sensitive detailed pricing.

Before implementation, approve event types, recipients, sender domain, provider, retry policy, escalation owner, and retention. When asynchronous delivery is introduced, use a transactional outbox or equivalent database-backed handoff so a committed business event cannot be lost between Django and the worker.

## 9. Backup, recovery, and retention

DBGI IT and management must approve recovery point and recovery time objectives. Until approved, do not promise a recovery window.

The production plan must include:

- Automated encrypted PostgreSQL backups.
- Automated encrypted attachment backups or versioned private object storage.
- Off-VPS storage with restricted access and documented retention.
- Backup-failure alerts with a named owner.
- Regular restore tests into an isolated environment.
- A runbook for database, attachment, VPS, credential, and region or provider failure.
- Documented record retention, deletion, legal hold, and audit preservation rules.

A database dump alone is insufficient because it does not contain private attachment bytes.

## 10. Monitoring and operations

Monitor external uptime, HTTP error rates, application exceptions, database capacity, disk usage, backup results, certificate expiry, container health, and authentication or throttling anomalies. Send actionable alerts to named DBGI owners.

Use structured application logs with request correlation while excluding secrets and protected content. Define severity, response time, escalation, maintenance windows, and incident communication before launch. Keep a tested procedure for secret rotation and administrator lockout recovery.

## 11. Capacity and scaling

Begin with one appropriately sized VPS only after staging load tests establish CPU, memory, database, and storage needs. Do not select a production size from development usage alone.

Scale in this order when evidence requires it:

1. Tune application queries, indexes, Gunicorn workers, and PostgreSQL settings.
2. Move attachments to private object storage.
3. Add background workers for slow or scheduled jobs.
4. Separate PostgreSQL onto a managed or dedicated private service if availability, backup, or load requires it.
5. Add multiple web nodes only with shared sessions, cache, attachments, and a reviewed load-balancing design.

## 12. Acceptance and launch gates

Production launch requires documented evidence for all of the following:

- Product owners approve lifecycle, matching, ranking, pricing, renewal, reorder, and exception rules in launch scope.
- Security owners approve the permission matrix, attachment handling, Cloudflare, firewall, TLS, cookies, headers, and administrator access.
- `DEBUG=False` and Django deployment checks pass with production-like settings.
- Migrations succeed on a production-like database and have a reviewed recovery plan.
- Company-isolation tests cover lists, detail endpoints, files, direct identifiers, rankings, reports, and exports.
- PostgreSQL concurrency tests pass for critical row-locked workflows.
- Frontend keyboard, dialog, focus, error, responsive, and browser workflows pass.
- Backup and attachment restore drills succeed and meet approved objectives.
- Monitoring and alerts reach named responders.
- Approved production master data is loaded without development accounts or sample transactions.
- A controlled pilot, support owner, rollback criteria, and incident contacts are documented.

## 13. Decisions and ownership required

| Decision | Proposed owner |
| --- | --- |
| React frontend divergence approval | DBGI product and technical owners |
| Lifecycle, matching, ranking, and tie policy | DBGI product owner |
| Pricing, VAT, rounding, and visibility | DBGI finance and pricing owner |
| Attachment formats, scanning, retention, and deletion | DBGI security, legal, and operations |
| Notification events, recipients, and provider | DBGI product and IT |
| Recovery objectives and backup retention | DBGI IT and management |
| VPS sizing, monitoring, and incident ownership | DBGI IT |
| Production permission matrix and access review | DBGI security and management |

Record each approval in a dated decision log. Unresolved decisions remain launch blockers and must not be silently inferred by engineering.
