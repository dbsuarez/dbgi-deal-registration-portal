# API Standards - Django Ninja

## Contracts and routing
- Use Django Ninja routers grouped by business domain.
- Use predictable resource-oriented URLs and consistent HTTP methods.
- Use typed request and response schemas; do not return unrestricted Django model objects or confidential fields.
- Publish and maintain OpenAPI documentation.
- Version public APIs when compatibility requires it.

## Querying
- Validate pagination, search, sorting, and filtering parameters.
- Apply permission and tenant/branch scope before pagination.
- Use server-side pagination for large collections.
- Allow sorting only by explicitly permitted fields.
- Prevent N+1 queries with `select_related`, `prefetch_related`, and targeted querysets.

## Errors
- Return consistent machine-readable error codes and understandable user messages.
- Use appropriate HTTP status codes, including 400/422 for invalid input as applicable, 401 for unauthenticated, 403 for forbidden, 404 for absent or hidden records, 409 for conflicts, and 429 for throttling.
- Do not leak stack traces, database details, or secrets.
- Make validation errors map cleanly to frontend fields.

## Reliability
- Use database transactions for multi-step writes.
- Use idempotency keys and constraints for critical operations.
- Use optimistic concurrency checks where conflicting edits are possible.
- Define timeouts and retry policies for external integrations.
- Validate and authorize all requests server-side.

## Review checklist
- [ ] Schema, permissions, and error contracts are tested
- [ ] Queries are scoped and efficiently paginated
- [ ] Critical writes are transactional and duplicate-safe
- [ ] API documentation reflects actual behavior
