# Security Standards - Django

## Authentication and sessions
- Prefer Django's established password hashing and authentication mechanisms.
- Choose secure cookie-based sessions or appropriately designed token authentication based on client architecture.
- If using cookie authentication, configure CSRF protection correctly; do not disable it to fix frontend integration issues.
- Use secure, HttpOnly cookies where applicable and appropriate SameSite settings.
- Apply session expiry, login throttling, and secure recovery flows.

### Development-only login accounts

Projects may provide a password-free account chooser to make local development and role testing faster. When provided, use the following starter-kit convention:

- Keep development authentication utilities in a dedicated `devtools` Django app, separate from business-domain apps.
- Show accounts grouped by meaningful role or account type, such as company users and administrators.
- Keep the normal username and password form available and provide an obvious Django Admin link when the project uses Django Admin.
- Provision predictable local accounts through an idempotent `seed_development_accounts` management command. Document the usernames and shared local password in the project README.
- Gate the chooser, its login endpoint, and the seeding command with `settings.DEBUG`. The endpoint and command must fail closed when `DEBUG=False`.
- Require POST and CSRF protection for password-free login. Accept only active users and validate any redirect destination as a local, allowed URL.
- Never create development accounts in a schema or data migration, container startup, deployment script, or production database.
- Never reuse development passwords for staging or production accounts. Treat a deployment with `DEBUG=True` as a release-blocking security defect.
- Test successful development login, role grouping, redirect validation, and denial when `DEBUG=False`.

### Development-only scenario controls

Projects may provide a repeatable scenario loader for local workflow testing. When provided:

- Keep it inside the dedicated `devtools` app and require both `settings.DEBUG` and a true Django superuser.
- Hide its navigation entry and return not found when either condition is absent.
- Require POST and CSRF protection for every scenario load.
- Explain expected records and workflow outcomes before execution.
- Make data clearing optional and require an exact typed confirmation phrase before deleting records.
- Define transactional and preserved master-data boundaries explicitly. Preserve users, companies, products, permissions, and login accounts unless a separate approved tool states otherwise.
- Perform clearing and scenario creation in one database transaction so partial scenarios are not left behind after an error.
- Delete attachment files through the application storage lifecycle rather than direct filesystem operations.
- Test superuser access, ordinary administrator denial, production denial, confirmation failure, scenario outcomes, and preserved master data.

## Authorization
- Enforce role and object-level permissions in backend endpoints and querysets.
- Default to least privilege and prevent cross-tenant or cross-branch access.
- Treat Django Admin as a privileged maintenance interface with restricted access.
- Do not treat hidden frontend controls as authorization.

## Application hardening
- Configure `DEBUG=False`, `ALLOWED_HOSTS`, CSRF trusted origins, security middleware, HTTPS, and secure proxy settings for production.
- Keep secrets out of repositories and logs.
- Validate uploads by size, content type, and actual content as appropriate; store uploads safely.
- Use ORM parameterization, safe templates, and correct CORS configuration.
- Apply rate limits to sensitive endpoints.
- Avoid storing raw payment card information; use hosted/tokenized payment integrations.

## Logging and incident response
- Log authentication events, privilege changes, and sensitive administrative actions without secrets or unnecessary personal data.
- Monitor exceptions and suspicious activity.
- Define backups, restore drills, secret rotation, and dependency update practices.

## Review checklist
- [ ] Authentication and CSRF/session design verified
- [ ] Development login is absent or fails closed when `DEBUG=False`
- [ ] Object-level access and data isolation tested
- [ ] Production security settings reviewed
- [ ] Uploads, secrets, logs, and rate limits reviewed
