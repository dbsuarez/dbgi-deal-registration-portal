# Testing and Quality Standards - Django

## Test layers
- Backend: pytest + pytest-django for models, permissions, services, and Django Ninja endpoints.
- Frontend: Vitest for components and utilities.
- End-to-end: Playwright for representative user workflows.
- Add integration tests for database transactions, external APIs, and asynchronous work when relevant.

## Critical scenarios
- Authentication, session expiry, CSRF where applicable, and role/object-level permissions
- Create, view, update, archive/delete, and validation
- Unique constraints and concurrent edits
- Calculations, status transitions, and audit trails
- Duplicate submission prevention and idempotent critical operations
- Pagination, filtering, sorting, and tenant scoping
- Empty, loading, failure, and offline UI states
- Keyboard navigation and accessibility of dialogs and contextual help

## Quality gates
- Run `python manage.py check` and `python manage.py check --deploy` against an appropriate production-like configuration.
- Run `python manage.py makemigrations --check --dry-run` to catch uncommitted model changes.
- Run configured pytest, Ruff, type checks, frontend linting, and builds.
- Do not run destructive migration commands against production without approval.
- Never claim a test passed unless it actually executed.

## CI/CD
Use GitHub Actions to run backend and frontend checks before deployment. Keep test credentials isolated and use disposable databases. Require migration review and backup readiness for risky deployments.

## Completion report
Summarize files changed, migrations generated, tests/checks executed, results, skipped checks, and remaining risks.
