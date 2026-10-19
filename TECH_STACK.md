# Django Technology Stack

## Scope
Default stack for AI-built business management systems with optional consumer-facing PWAs. This is a separate Django alternative to the existing FastAPI technology stack.

## Core stack
| Layer | Default |
|---|---|
| Server OS | Ubuntu 24.04 LTS |
| Backend | Python 3.13 + compatible, supported Django release |
| API | Django Ninja |
| Validation | Django Ninja schemas and Pydantic |
| ORM | Django ORM |
| Migrations | Django migrations |
| Database | PostgreSQL 17 or a supported PostgreSQL release |
| Web frontend | React + TypeScript, PWA |
| UI | MUI, MUI X Data Grid where appropriate |
| Barcode / QR | Browser camera API with ZXing JS where required |
| Charts | Recharts where required |
| Background jobs | Scheduler or task worker selected to fit deployment; Celery + Redis for distributed processing when justified |
| Storage | S3-compatible object storage, such as Cloudflare R2 |
| Reverse proxy | Nginx + HTTPS |
| DNS / edge security | Cloudflare |
| Packaging | Docker + Docker Compose |
| Error monitoring | Sentry |
| Uptime monitoring | Uptime Kuma plus independent off-server monitoring |
| CI/CD | GitHub Actions |
| Tests | pytest, pytest-django, Playwright, Vitest |
| Code quality | Ruff, MyPy where configured, ESLint, Prettier |
| Documentation | Django Ninja OpenAPI and project docs |

Pin exact package versions after checking current support and compatibility. Do not assume a particular Django version supports every dependency.

## Architecture
Cloudflare -> Nginx -> React PWA and Django ASGI/WSGI application -> PostgreSQL and object storage.

Keep the React + MUI interface as the primary user-facing application. Django Admin is an optional, restricted maintenance interface, not a replacement for the UI standards.

Organize backend features into focused Django apps. Keep API schemas, endpoints, services, selectors/query logic, permissions, and models separate when complexity warrants it. Do not create abstractions without a practical need.

## Deployment and scaling
Start with a single correctly configured deployment when appropriate. Configure `ALLOWED_HOSTS`, CSRF trusted origins, secure cookies, proxy headers, static/media storage, database connections, and HTTPS carefully. Do not use Django's development server in production.

Scale the web tier and database independently when required. For scheduled work, avoid duplicate execution across multiple replicas; use a dedicated worker/scheduler or distributed task system. Back up PostgreSQL and media off-site and test restores.

## AI agent guidance
Use this file alongside `AGENTS.md` and the dedicated standards. Never migrate an existing FastAPI project to Django without explicit approval.
