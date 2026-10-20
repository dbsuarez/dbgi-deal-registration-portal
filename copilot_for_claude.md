# Claude handoff: DBGI Project Registration Portal

> Superseded architecture notice, 2026-10-19: the server-rendered UI and Caddy deployment described below were replaced by the repository-standard React, TypeScript, MUI, Django Ninja, PostgreSQL 17, Python 3.13, and Nginx stack. Use `TECH_STACK.md`, `AGENTS.md`, and `README.md` as the current technical sources of truth. The business decisions and unresolved policies in this historical handoff and the v9 working specification remain relevant.

Updated: 2026-10-17

## Purpose and product decisions

This is an initial implementation of DBGI's company-scoped project/deal-registration portal. Read [`docs/DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md`](docs/DBGI_Project_Registration_Portal_Design_Working_Spec_v9.md) before changing business behavior; it is the detailed source of truth for decisions and unresolved policies.

The user chose Django with server-rendered templates for quickest delivery, PostgreSQL for deployment, and Docker on a Hostinger VPS. The reference Canon Partner Portal was inspected and a clearly fake test registration was created, edited, then deleted from that non-live site with the user's permission. Canon observations are inspiration only; they are not DBGI rules.

## What has been done and why

The work so far establishes a **small, working, inspectable foundation**, rather than attempting to implement the entire portal before the business rules and operating decisions are settled.

| Work completed | Why it was done |
| --- | --- |
| Inspected the visible Canon registration flow and recorded the useful patterns separately from DBGI requirements. | Use the reference to understand familiar interactions without accidentally adopting another company's statuses, policies, or hidden behavior. |
| Recorded the user's initial form, competitor, requested-price, picker, and evidence decisions in the v9 working spec. | Give implementation a documented baseline and make unresolved decisions visible instead of guessing. |
| Chose Django templates, PostgreSQL for deployment, Docker, and a Hostinger VPS target. | The user prioritized the quickest practical launch; Django provides authentication, forms, ORM, migrations, and admin in one stack, while the container/VPS path fits the intended deployment. |
| Built a company-user flow to sign in, submit/edit registrations, and view the registration list and details, with repeatable competitor/product/evidence rows. | Provide an end-to-end slice that can be previewed and tested before expanding the workflow. |
| Added server-side company scoping, DBGI-admin access, and submission/edit audit snapshots. | Protect partner-specific commercial information and preserve an initial change history; browser-side hiding alone is not sufficient. |
| Added a built-in Django admin interface for companies, users, products, registrations, attachments, and events. | Give administrators basic data-management and review access now, before investing in a custom review dashboard. This is intentionally not the complete approval/ranking UI. |
| Added private attachment storage/download authorization, file-extension/size checks, and a database health endpoint. | Establish the evidence-handling and operational foundations required by the selected registration flow. The attachment controls still need production security/retention decisions. |
| Added Docker Compose for PostgreSQL and the Django app, plus Caddy HTTPS proxy configuration and a setup/operations README. | Make the selected VPS deployment path repeatable while keeping the database and app ports off the public host interface. |
| Created fake local preview data and preview accounts, and validated the main flow, migrations, Docker build, PostgreSQL smoke test, and proxy config. | Let the user inspect both company and admin screens without entering real partner/project information, and catch integration issues early. Preview credentials/data are local-only and must not be deployed. |

**Why the larger workflow is not implemented yet:** the specification still marks important behaviors as undecided or requiring further implementation, including final status transitions, project/lot matching and ranking, discount approval/renewal, reorder verification, price history, VAT/rounding, notification policy, and production file/backup operations. These affect data models and commercial outcomes, so inventing them would create rework and could apply the wrong DBGI policy. Consult the spec and ask the user when a decision is needed.

User-confirmed initial registration requirements:

- Partner account comes from the authenticated user's assigned company; collect end-user name/address, project title, bid and delivery dates, and contact information.
- Require at least one competitor item: brand, item/model, bid price, and remarks.
- Let a company request prices for catalog or non-catalog product lines. Requested prices are proposals, not approved prices.
- Require an evidence description and authorization-to-share confirmation. A public link and private evidence attachments are optional.
- Do not copy Canon status labels or invent approval, ranking, VAT, pricing, or other workflow policy. Use the spec and ask the user when an undecided policy materially affects implementation.

## Implemented so far

### Application and access control

- Django project in `config/`; registration app in `registrations/`.
- Custom user has Company and DBGI-admin roles and an optional company assignment.
- Company users' registration list, detail, edit, and attachment-download access is company-scoped server-side. DBGI admin/superuser can see all registrations.
- Company users cannot access Django `/admin/`; DBGI admins and superusers can.
- Built-in Django admin is currently the only DBGI admin UI. It manages companies, users, products, registrations and their competitor/product rows, attachments, and read-only registration events. It is not the purpose-built review dashboard or complete decision workflow.
- Registration form supports repeatable competitor, product, and attachment rows; at least one competitor and product line are required.
- Registration edits set `needs_review` and append an event with a snapshot of the pre-edit registration.
- Initial submissions append an event snapshot of the submitted registration.
- Health endpoint is `/health/` and checks the database with `SELECT 1`.

### Evidence and attachments

- Evidence description and sharing attestation are required; optional evidence URL is supported.
- Attachment prototype limits: 10 MiB maximum and PDF, PNG/JPG/JPEG, DOCX, XLSX extensions. Names stored on disk are random UUIDs under `private/registrations/`.
- Attachment downloads require login and access to the parent registration's company (or DBGI admin); responses use `application/octet-stream` and `Cache-Control: private, no-store`.
- Deleting an attachment record deletes its file after the database transaction commits.
- These attachment defaults are prototype choices, not finalized DBGI retention/security policy. There is no file-content inspection or malware scanning yet. See the corresponding note in the design spec.

### Data models

Current domain models: `Company`, custom `User`, `Product`, `Registration`, `CompetitorItem`, `RegistrationItem`, `RegistrationEvent`, `RegistrationAttachment`.

- `Registration.Status` currently contains `submitted`, `under_review`, `approved`, `rejected`. These are starter states, not a finalized workflow transition model.
- Product records contain code/name/category and active flag; no SRP or price-history models exist yet.
- Migration `0003_seed_initial_laser_printers.py` seeds the two user-selected initial catalog products M1820W and P1820W as active `Laser Printers`, with the shared name `20 ppm monochrome laser printer` and no price. Other public-page product examples remain reference-only. No real partner accounts or prices are seeded.
- No separate procurement-opportunity model, matching/ranking engine, approved discount model, reorder flow, notifications, or reporting/export workflow has been implemented.

### Main files

- `config/settings.py`, `config/urls.py`: environment-based settings, local SQLite fallback, PostgreSQL configuration, proxy/HTTPS flags, health and login routes.
- `registrations/models.py`, `forms.py`, `views.py`, `urls.py`, `audit.py`, `admin.py`, `middleware.py`: core app, forms, company scope, audit snapshots and admin.
- `registrations/migrations/0001_initial.py` through `0003_seed_initial_laser_printers.py`: current schema and two initial product seeds.
- `templates/` and `registrations/static/registrations/`: server-rendered UI and progressive enhancement.
- `registrations/tests.py`: focused regression/security behavior tests.
- `Dockerfile`, `docker-compose.yml`, `Caddyfile`, `.env.example`: container, PostgreSQL, and Caddy HTTPS setup.
- `README.md`: local/Docker setup and operations notes.

## Running and preview state

- Local development uses SQLite (`db.sqlite3`) unless `DB_HOST` is set. Compose supplies PostgreSQL variables and uses PostgreSQL.
- The local preview was migrated, and a fake company/registration/product plus separate preview company/admin accounts were added to the ignored local SQLite database. Do not deploy or copy this database, its accounts, or demo records to production. Do not put preview passwords or secrets in this handoff or source control.
- The Django development server was started on `127.0.0.1:8000` with `--noreload` and was still running during the last preview. Reuse it if still up; if the port is occupied, inspect the existing process rather than starting a competing server. This local server is not public deployment.
- Local setup: create/activate `.venv`, install `requirements.txt`, run `python manage.py migrate`, then `python manage.py runserver`.
- Admin entry point: `/admin/`. To make a new local admin, use `python manage.py createsuperuser`; don't rely on preview credentials for deployment.
- Docker setup and initial VPS notes are in `README.md`. Compose exposes only Caddy on ports 80/443; the web app is reachable only on Docker networks; the PostgreSQL network is marked internal. `.env` is ignored and must contain unique production secrets.

## Verification already performed

Latest recorded validation:

- `python manage.py test registrations --verbosity 2`: all 10 tests passed, including company isolation, evidence validation, attachment type/size validation, authorized downloads, and post-commit file cleanup.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no migration drift.
- Docker Compose configuration validation and application image build passed.
- A temporary PostgreSQL-backed Compose smoke test applied migrations, started Django, and got `{"status": "ok"}` from `/health/`.
- Caddy configuration validation passed.
- Temporary `.env` files and temporary Compose resources used for these checks were removed.

Rerun checks after edits; don't assume these validations cover new code.

## Deployment and security boundaries

- Target is `registration.dbgi.ph` on the user's Hostinger VPS, not Hostinger Business shared hosting. No live deployment or DNS/firewall changes have been made.
- Docker Compose uses PostgreSQL 16 Alpine, Gunicorn, WhiteNoise, and Caddy TLS. Configure DNS, firewall ports 80/443, strong unique secrets, allowed hosts and CSRF origin before starting a deployment.
- Do not turn on HSTS until HTTPS is verified. Do not expose PostgreSQL or Gunicorn directly to the Internet.
- Backup instructions in `README.md` cover PostgreSQL; private `media_data` must also be backed up independently. Off-VPS backup, retention and restore procedures still need to be established and tested.
- Current extension/size checks do not verify file contents. Add a considered malware/file-scanning and retention approach before accepting real evidence in production.

## Important open work

1. Build a DBGI-oriented review dashboard and explicit, audited transitions/permissions; document and implement matching/ranking, evidence decisions, material-edit review and company notices from the spec.
2. Resolve the required-field matrix, opportunity/lot representation, project-status transition table, expiry/reminder settings, PHP VAT/rounding, price selection/version timing, and other remaining questions called out in the spec. Ask the user; do not infer policy.
3. Implement opportunity matching/ranking only after review decisions; ranking is per DBGI-confirmed opportunity/lot and based on original eligible server-recorded submission times.
4. Implement product price history and visibility rules, discount approvals/renewals, reorder verification/corrections, durable notifications and exports according to the spec. Server-side calculations and authorization remain authoritative.
5. Enter DBGI-approved catalog and partner data through admin/import; do not promote public-page examples into production products or invent prices.
6. Complete production operations: tested database and media backups/restores, retention, monitoring, file scanning, incident response and Django deployment checklist. No deployment should happen without the user's authorization.
7. Review admin-event snapshot behavior when editing child inlines; the current admin event snapshot is captured before the admin save and may not fully represent all child-row changes.

## Working conventions for the next contributor

- Preserve the user decisions in the v9 spec; reference-only Canon behavior is not DBGI policy.
- Keep changes focused, company-scoped, server-validated and auditable. Do not expose another company's registrations, competitor data, evidence, or price terms.
- Add tests for behavioral/security changes and run the focused Django checks above.
- Never commit `.env`, local `db.sqlite3`, preview credentials, uploaded evidence, backups, or production secrets.
- The repository did not have Git initialized when implementation began; inspect the current workspace before assuming branch/commit state.
