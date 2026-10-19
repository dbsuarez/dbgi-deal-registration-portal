# DBGI Project Registration Portal

Company-scoped project registration portal built with Django Ninja, React, TypeScript, MUI, and PostgreSQL. Nginx serves the React application and proxies authenticated Django operations.

## Run locally

Requires Python 3.13 and Node.js 24 for the selected starter-kit stack.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_development_accounts
python manage.py runserver
```

In a second terminal, start the React development server:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/`. The React development server proxies API, authentication, admin, and attachment routes to Django on port 8000. API documentation is available to authorized developers at `/api/v1/docs` through Django.

The debug login shows the `preview` company account and `admin-preview` DBGI administrator account. Both use `testpass123` for standard password login. The password-free chooser and the account-seeding command are disabled when `DEBUG=False`. See the development-only login policy in [`SECURITY_STANDARDS.md`](SECURITY_STANDARDS.md).

Two initial laser printer catalog entries (M1820W and P1820W) are added by migration without prices. Production partner and administrator accounts are never seeded automatically.

## Run with Docker

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

The Django process and database are not published to the host. Nginx is the only public Compose service, and PostgreSQL is on an internal Docker network. After HTTPS is confirmed, consider setting `DJANGO_SECURE_HSTS_SECONDS` to a conservative value and verify the Django deployment checklist before production use.

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
npm run lint
npm run test
npm run test:e2e
npm run build
```

## Current scope

This is the initial registration and DBGI review foundation. Workflow states, ranking/approval transitions, conditional required-field rules, VAT/rounding, discount validity, catalog data, notifications, backup automation, and production operating procedures still need DBGI decisions or implementation. Do not treat the starter statuses or this setup as production approval of those policies.
