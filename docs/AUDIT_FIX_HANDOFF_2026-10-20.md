# Audit fix handoff, 2026-10-20

Read this before touching the registration portal again. Ten local commits fix the critical and high findings from the audit. Nothing is pushed yet. The remote is `https://github.com/dbsuarez/dbgi-deal-registration-portal.git` on `main`.

The audit report itself lives outside the repo at `C:\Users\cha0s\OpenBot\Agents\agent-5053dd64-ba33-4ac9-8bcd-7ca01311fbd2\audit-project-registration-portal.md`.

## Commits, oldest first

| Commit | Subject |
| --- | --- |
| `0028c88` | Fail closed on DEBUG and mount the debug login only in debug |
| `77b4257` | Lock evidence changes and validate attachment content |
| `031c603` | Treat equal top match scores as ambiguous |
| `375c2cd` | Lock the registration while refreshing a matching suggestion |
| `7710e65` | Bump and audit the version on admin edits |
| `52bc5b1` | Refuse to clear transactional records outside debug |
| `fc7cba8` | Add a finalize step so a submitted form is version-complete |
| `4ad002e` | Surface session and suggestion failures instead of swallowing them |
| `a930631` | Add the migration for attachment content validation |
| `2b45366` | Apply the formatter to files that predated this pass |

## Behavior changes you must know about

### 1. DEBUG now defaults to false

`config/settings.py` reads `DJANGO_DEBUG` with a `false` default. With no environment at all, Django raises `ImproperlyConfigured` because `DJANGO_SECRET_KEY` is required outside debug. This is deliberate: the old default silently enabled the insecure secret, non-secure cookies, traceback pages, and the account chooser.

Local work now needs `$env:DJANGO_DEBUG = "true"` before `manage.py` or `runserver`. The README documents it.

Tests get their debug config from `config/settings_test.py`, which sets the environment before importing the real settings, plus `django_debug_mode = "keep"` in `pyproject.toml`. If you add a test that asserts production behavior, use `@override_settings(DEBUG=False)`.

`config/urls.py` mounts `accounts/debug-login/` only when `DEBUG` is true. The standard `accounts/login/` page stays mounted in production because it is the real login page; only its account chooser is debug-gated, inside `devtools/views.py`.

### 2. Evidence changes are locked and audited

`RegistrationAttachment` is guarded in `registrations/api.py` by `_attachment_edit_guard`, evaluated under `select_for_update` on the registration row.

- Adding or deleting evidence is refused with `409 evidence_locked` when the status is `under_review`, `approved`, or `rejected`. The set lives at `Registration.EVIDENCE_LOCKED_STATUSES`. `eligible_matched` stays editable because a company edit already reverts it to `review_required`.
- A mismatched registration version returns `409 edit_conflict`.
- Every change writes a `RegistrationEvent` (`Attachment added`, `Attachment removed`) whose snapshot is the state before the change.
- Magic bytes are validated in `registrations/models.py` by `validate_attachment_content`. Allowed containers: PDF, PNG, JPEG, DOCX, XLSX. ZIP-based Office files accept the `PK\x03\x04` header.

### 3. Attachment API contract changed

These are breaking changes for any client other than the React app, and the React app is updated.

- `POST /api/v1/registrations/{id}/attachments` now requires a `version` query parameter.
- `DELETE /api/v1/attachments/{id}` now requires a `version` query parameter and declares `400`, `404`, `409` in addition to `204`.
- `POST /api/v1/registrations/{id}/finalize` is new. Body: `{ "version": int, "evidence_changed": bool }`. It re-checks the version under a row lock, bumps the registration version once, sets `needs_review` when evidence changed, writes an `Evidence submitted` event, and returns a `RegistrationListItem`.

Uploads and deletes deliberately do not bump the registration version. The form holds one version for the whole save, and finalize is the single commit point. Without this, a form with three uploads would need to track three intermediate versions.

### 4. Finalize is what makes a submit complete

`frontend/src/pages/RegistrationFormPage.tsx` saves fields, transfers files, then calls `finalizeRegistration` when anything was uploaded or deleted. A crash between the file transfers and finalize leaves the registration at its pre-save version, which is the intended signal that the submit did not finish.

### 5. Matching ties no longer guess

`registrations/matching.py` collects every candidate at the top score. More than one means `CLARIFY` at `MEDIUM` confidence with no candidate scope and no auto-match. Exact-match ties keep the original message, because a test and the reviewer UI text depend on it.

Auto-match still requires exactly one exact candidate, no conflicts, and an automatchable status.

### 6. Admin edits invalidate stale clients

`RegistrationAdmin.save_model` snapshots the prior state from the database, increments `version`, and stores it read-only in the change form. The `Admin update` event records the resulting version. Before this, a company form loaded before an admin edit could save over it.

### 7. Destructive development clear is gated

`devtools/scenarios.clear_transactional_records` raises `CommandError` when `DEBUG` is false, instead of trusting its callers.

### 8. Frontend failure handling

- `App.tsx` shows the session load failure with a retry instead of an endless spinner.
- `RegistrationDetailPage.tsx` guards the refresh-suggestion button with a busy state and reports failures inline, leaving the page usable.
- `api.ts` mutation requests now keep the `?next=` parameter on a 401, matching plain requests.

## Database

One new migration: `registrations/migrations/0010_alter_registrationattachment_file.py`. It changes only the field validators, no columns. There is no data migration.

## Tests added

- Equal top match scores resolve to clarify, with no candidate and no auto-match.
- Attachment upload and delete write audit events.
- Attachment changes are refused after review starts.
- Attachment changes are refused on a stale version.
- A PDF with executable header bytes is rejected.
- `finalize` bumps the version and rejects a stale one.
- Admin `save_model` bumps the version and keeps the prior snapshot.
- `clear_transactional_records` refuses outside debug.

## Verification, all run on 2026-10-20

```
python manage.py check                 -> no issues
python manage.py makemigrations --check --dry-run -> no changes
pytest -q                              -> 44 passed
ruff check .                           -> all checks passed
ruff format --check .                  -> 40 files already formatted
npx tsc -b                             -> clean
npm run lint                           -> clean
npm test                               -> 1 file, 1 test passed
```

Playwright e2e was not run because it needs Django and the Vite server running. It touches the form path that changed, so run it before merging.

## Deliberately not done

- No `version` field on `RegistrationAttachment`. The registration version under a row lock already covers the delete race, and a second version would need another client-visible field for no additional protection.
- `update_registration` still has no status gate. Evidence is frozen, but a company can still edit fields during `under_review`, which sets `needs_review` and moves the record to `review_required`. That is existing product behavior, not something this pass changed.
- The medium and low findings are untouched: throttling, missing indexes, the N+1 in the matching loop, the error contract (`code` and `details` are still discarded in `api.ts`), admin authorization by URL prefix, the missing 404 route, and the rest.

## Correction to the audit report

The report and an independent reviewer flagged `registrations/migrations/0009_seed_common_philgeps_end_users.py` for corrupted text, `Concepcion PequeAa`. That is wrong. The bytes are UTF-8 `Concepcion Pequeña` (U+00F1 followed by `a`); the corruption was an artifact of how the file was displayed. No repair migration was written, and none is needed. Do not "fix" that literal.
