# Security Standards - Django

## Authentication and sessions
- Prefer Django's established password hashing and authentication mechanisms.
- Choose secure cookie-based sessions or appropriately designed token authentication based on client architecture.
- If using cookie authentication, configure CSRF protection correctly; do not disable it to fix frontend integration issues.
- Use secure, HttpOnly cookies where applicable and appropriate SameSite settings.
- Apply session expiry, login throttling, and secure recovery flows.

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
- [ ] Object-level access and data isolation tested
- [ ] Production security settings reviewed
- [ ] Uploads, secrets, logs, and rate limits reviewed
