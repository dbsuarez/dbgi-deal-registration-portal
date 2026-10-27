# AGENTS.md - Django Project Instructions

## Source of truth
This package is for projects that explicitly select **Django + Django Ninja**. It does not supersede or modify the separate FastAPI standards package.

Read `TECH_STACK.md` first, then the relevant standards for the task:
- Frontend and user experience: `UI_STANDARDS.md`
- Backend APIs: `API_STANDARDS.md`
- Database changes: `DATABASE_STANDARDS.md`
- Authentication, authorization, and data protection: `SECURITY_STANDARDS.md`
- Verification: `TESTING_STANDARDS.md`
- Word or slide learning guides (DeckCraft and WordCraft CLIs): `docs/guides/_source/CLI_NOTES.md`; shared notes and helpers for all ArtCraft tools: https://github.com/dbsuarez/artcraft-usage (local clone `D:\Developmentrtcraft-usage`)

If rules conflict, identify the conflict and request clarification rather than silently choosing. Project-specific requirements may add constraints, but do not silently weaken security or data-integrity standards.

## AI agent execution workflow
1. Inspect existing code, dependencies, tests, and conventions before editing.
2. Plan substantial features, including models, API contracts, permissions, migrations, and tests.
3. Prefer Django's established facilities over custom reimplementations.
4. Make focused, complete changes. Avoid unnecessary rewrites and unfinished placeholders.
5. Obtain approval before destructive data changes, irreversible operations, or major architectural changes.
6. Add or update migrations, tests, and documentation as applicable.
7. Run available checks and tests. Never claim a check passed unless it ran.
8. Report files changed, migrations, checks run, outcomes, and remaining risks.

## Mandatory global rules
- Never use en dashes or em dashes in code, comments, documentation, or UI text. Use a normal hyphen instead.
- Follow `UI_STANDARDS.md` for the existing table-first UX, grid layouts, formatting, accessible contextual help, forms, and interaction patterns.
- All displayed dates use `YYYY-MM-DD`; timestamps with time use `YYYY-MM-DD HH:mm` where needed.
- Numeric and currency text, including corresponding table headers, must be right-aligned.
- Do not edit records inline in tables. Use modal forms for simple edits and dedicated pages for complex forms.
- Do not expose sensitive information or trust frontend permissions alone.
- Keep framework-specific backend rules in this Django package, not the FastAPI package.

## Completion checklist
- [ ] Existing behavior and relevant standards reviewed
- [ ] Django models, constraints, permissions, and migrations considered
- [ ] API input and output schemas validated
- [ ] UI follows `UI_STANDARDS.md`
- [ ] Security, errors, and concurrency addressed
- [ ] Tests and static checks executed where available
- [ ] Results and limitations accurately reported
