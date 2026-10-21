# DBGI Project Registration Portal

Company-scoped project registration portal built with Django Ninja, Django Unfold, React, TypeScript, MUI, and PostgreSQL. Nginx serves the React application and proxies authenticated Django operations.

## Run locally

Requires Python 3.13 and Node.js 24 for the selected starter-kit stack.

`DEBUG` defaults to off. Set it explicitly for local work:

```powershell
$env:DJANGO_DEBUG = "true"
```

Then:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_development_accounts
python manage.py seed_sample_matching_scenario
python manage.py runserver
```

In a second terminal, start the React development server:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/`. The React development server proxies API, authentication, admin, and attachment routes to Django on port 8000. API documentation is available to authorized developers at `/api/v1/docs` through Django.

### Windows development with local-network access

Use two PowerShell terminals. These commands make the portal available on this computer and to testers on the same local network. Replace `192.168.100.100` everywhere below if the development computer's local IP address changes.

In the first terminal, start Django:

```powershell
Set-Location D:\Development\project-registration-portal

$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.100.100"
$env:DJANGO_CSRF_TRUSTED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://192.168.100.100:5173"

.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_development_accounts
python manage.py runserver 0.0.0.0:8000
```

In the second terminal, start React:

```powershell
Set-Location D:\Development\project-registration-portal\frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open one of these URLs:

- This computer: `http://127.0.0.1:5173/`
- Local network: `http://192.168.100.100:5173/`
- Django Admin: `http://192.168.100.100:5173/admin/`
- API documentation: `http://192.168.100.100:5173/api/v1/docs`

After dependencies and migrations are installed, the ordinary daily startup only requires the environment variables, Django `runserver`, and the React development server. Keep both terminal windows open while testing.

After every `git pull`, apply any new migrations before opening the portal. This prevents the running backend from querying columns that the local database does not have yet:

```powershell
$env:DJANGO_DEBUG = "true"
python manage.py showmigrations registrations
python manage.py migrate
```

The debug login shows the `preview` company account and `admin-preview` DBGI administrator account. Both use `testpass123` for standard password login. The password-free chooser and the account-seeding command are disabled when `DEBUG=False`. See the development-only login policy in [`SECURITY_STANDARDS.md`](SECURITY_STANDARDS.md).

`seed_sample_matching_scenario` adds an IT Avenue registration already matched to a sample printer-procurement lot and a later Lexmark registration that is automatically matched to the same scope. Automatic matching requires exactly one scope with identical normalized End-user and address values, complete catalog-product overlap, and no conflicts. Ambiguous or partial matches remain pending for administrator review. The sample company accounts are `deals@itavenue.ph` and `deals@lexmark.com`, both with the local-only password `testpass123`.

Django superusers can open **Administration > Scenario Lab** in Django admin while `DEBUG=True`. The lab explains and loads automatic-match, ambiguous-match, and material-edit scenarios. It can optionally clear transactional registrations, opportunities, scopes, items, attachments, events, suggestions, and review decisions after the user types `CLEAR TRANSACTIONS`. Companies, users, products, permissions, and login accounts are always preserved. The panel is hidden from ordinary administrators and unavailable when `DEBUG=False`.

## End-user directory

Registrations select an End-user from shared master data instead of entering a new name and address each time. DBGI administrators maintain the directory in Django Admin under **Master data > End-users**. Records include organization classification, address, PhilGEPS reference details, aliases, verification status, source, and audit fields.

If a company cannot find the organization, it can use **Add missing End-user** on the registration form. The proposal is immediately available to that company with **Pending verification** status. Its registration can be submitted, but it cannot be automatically matched or ranked until an administrator verifies the End-user. Pending proposals from one company are not visible to other companies.

Administrators should compare proposals with an authoritative source, correct the official name and address if necessary, add useful aliases, and use **Verify selected End-users**. Business records are archived with `is_active` instead of being deleted. Existing registration and opportunity text is retained as an audit snapshot even though records are linked to the directory.

Migration `registrations.0009_seed_common_philgeps_end_users` provides a starter catalog based on the top procuring entities by bid and award notice volume in the PhilGEPS 2023 Statistical Bulletin. It also consolidates active duplicates only when both the normalized name and normalized address match, moves transaction links to the canonical record, and archives the redundant record for recovery.

## Visible build time

The portal footer displays the frontend build time as `YYYY-MM-DD HH:mm`. Vite stamps the current local time automatically when the frontend is built. A release pipeline can provide an explicit value through the `BUILD_TIME` environment variable. For example, in PowerShell:

```powershell
$buildTime = Get-Date -Format 'yyyy-MM-dd HH:mm'
$env:BUILD_TIME = $buildTime
npm run build
```

Docker builds accept the same value with `--build-arg BUILD_TIME="YYYY-MM-DD HH:mm"`. If no value is supplied, the Docker build uses its current local build time.

Multiple user accounts may belong to the same company. Manage them under **Master data > Users** in Django admin. These users share company-scoped records and count as one company in opportunity rankings.

Competitor brands are shared master data managed under **Master data > Competitor brands** in Django Admin. Canon, Epson, HP, and Lexmark are seeded initially, with Hewlett Packard mapped as an alias of HP. Company users may enter a new brand while adding a competitor item; a case-insensitive, whitespace-normalized master record is created when the registration is saved. An alias entry resolves to its canonical brand, so entering Hewlett Packard saves HP on the competitor item. Administrators can rename, archive, restore, search, and maintain aliases for these brands. Existing competitor items keep their saved brand text as a historical snapshot.

Two initial laser printer catalog entries (M1820W and P1820W) are added by migration without prices. Production partner and administrator accounts are never seeded automatically.

## Run with Docker

The proposed production architecture, security boundaries, operations, recovery requirements, and launch gates are documented in [`docs/TECHNICAL_INFRASTRUCTURE_PROPOSAL_2026-10-21.md`](docs/TECHNICAL_INFRASTRUCTURE_PROPOSAL_2026-10-21.md).

Requires Docker Engine and the Compose plugin. Copy `.env.example` to `.env`, set a unique Django secret and strong matching PostgreSQL passwords, and set `SITE_DOMAIN` to the DNS name pointed at this VPS. Do not commit `.env`.

The production architecture is Cloudflare HTTPS to Nginx, then React or Django depending on the route. Allow only the intended web ports in the VPS firewall. Configure Cloudflare origin protection and TLS before accepting real traffic.

```powershell
Copy-Item .env.example .env
# Generate a key with: python -c "import secrets; print(secrets.token_urlsafe(64))"
# Edit .env and replace all example secrets before continuing.
docker compose build
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose up -d
docker compose exec web python manage.py createsuperuser
```

The Django process and database are not published to the host. Nginx is the only public Compose service, and PostgreSQL is on an internal Docker network. After HTTPS is confirmed, consider setting `DJANGO_SECURE_HSTS_SECONDS` to a conservative value and verify the Django deployment checklist before production use. Enable `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` and `DJANGO_SECURE_HSTS_PRELOAD` only after confirming that every subdomain will remain HTTPS-only and the domain is ready for browser preload requirements.

Compose also runs an internal Redis cache used for request throttling across Gunicorn workers. Login submissions are limited per normalized username, and authenticated API mutations are limited per user. The defaults are documented in `.env.example`. Production fails closed for throttled operations if Redis is unavailable; local development and tests use Django's in-process cache unless `REDIS_URL` is configured.

In Django admin, create the DBGI partner companies and assign company users. The initial catalog migration seeds only the M1820W and P1820W laser printer examples selected by the user; it does not set prices. Other public-page product examples are not seeded. Add or update catalog entries and prices only from DBGI-approved data.

## Operations

- Check service status and logs with `docker compose ps` and `docker compose logs --tail=100 web nginx db`.
- Apply schema changes with `docker compose run --rm web python manage.py migrate`.
- Back up PostgreSQL to a private, ignored folder:

  ```powershell
  New-Item -ItemType Directory -Force .\backups
  docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB" -f /tmp/dbgi-portal.dump'
  docker compose cp db:/tmp/dbgi-portal.dump .\backups\dbgi-portal.dump
  docker compose exec -T db rm /tmp/dbgi-portal.dump
  ```

  Back up the `media_data` Docker volume separately; a database dump alone does not include evidence files. Store and test backups off the VPS.
- Keep `.env`, database dumps, uploaded evidence, and TLS material private. Establish and test retention, restore, monitoring, and incident-response procedures before production use.

## Verification

```powershell
python manage.py test registrations
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check config registrations
Set-Location frontend
npm run format:check
npm run lint
npm run test
npm run test:e2e
npm run build
```

`registrations.test_postgresql` contains concurrency tests that run only when `DB_HOST` selects PostgreSQL. Configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`, then run:

```powershell
python manage.py test registrations.test_postgresql
```

## Current scope

This internal beta includes company-scoped registration intake and editing, governed End-user and competitor-brand master data, evidence handling, DBGI review, deterministic matching, opportunity scopes, project status, permission-scoped rankings, category commercial approvals, item-level approved prices, expiry, 30-day approval renewals, and durable portal notifications for submission, registration, and price decisions. The Help page explains the post-submission procedure, and the Notifications page is the authoritative update channel while email policy remains unresolved. PostgreSQL concurrency behavior and the complete backend and frontend suites are configured as GitHub Actions quality gates.

It does not yet include withdrawal, opportunity merge or split, authoritative dated product-price versions, VAT and rounding policy, complete discount calculations, reorder processing, configurable email delivery, reports, production backup automation, or finalized operating procedures. Several lifecycle and pricing rules still require DBGI decisions. Do not treat the implemented starter behavior as production approval of unresolved policies.
