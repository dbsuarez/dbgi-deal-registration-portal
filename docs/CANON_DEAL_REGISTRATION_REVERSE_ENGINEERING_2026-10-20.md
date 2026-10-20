# Canon Partner Portal Deal Registration Analysis

Date started: 2026-10-20
Target: `https://partner.canon.com.ph/Deal-Registration`
Purpose: Product and workflow research for the DBGI Project Registration Portal

Authenticated walkthrough status: complete. See [CANON_DEAL_REGISTRATION_AUTHENTICATED_FINDINGS_2026-10-20.md](CANON_DEAL_REGISTRATION_AUTHENTICATED_FINDINGS_2026-10-20.md) for verified fields, status behavior, category approvals, audit history, implementation risks, and controlled-test cleanup.

## Scope and rules

This document records behavior observed through authorized use of the Canon Philippines Partner Portal. Testing must use a dedicated test account and clearly synthetic records. Test records may be created, edited, and deleted, but authentication controls must not be bypassed and other users' data must not be modified.

Every finding uses one of these evidence labels:

- **Observed**: directly visible in the user interface or an HTTP response.
- **Inferred**: strongly suggested by public client behavior or request contracts, but not confirmed as an internal implementation detail.
- **Recommendation**: a lesson proposed for the DBGI portal, not a claim about Canon's implementation.

## Current access boundary

### Observed

- Requesting `/Deal-Registration` without an authenticated session returns `302 Found` and redirects to `/Login?returnurl=%2fDeal-Registration`.
- The login page contains Username, Password, Remember Login, Login, Cancel, and Reset Password controls.
- The original Deal Registration URL is preserved as the return URL.
- The public page identifies itself as the Canon Partner Portal and shows copyright ownership as CMPI.
- The workflow, registration fields, record list, status values, edit rules, and deletion rules are not visible without authentication.

The authenticated workflow was subsequently tested. The findings are recorded in the companion document linked above.

## Publicly observable technical characteristics

### Observed

- The portal uses DNN, formerly DotNetNuke, with ASP.NET Web Forms artifacts including `__VIEWSTATE`, `__EVENTVALIDATION`, `ScriptResource.axd`, DNN modules, and DNN skin resources.
- The public assets load AngularJS, Angular Material, Angular Resource, and an Angular Material data-table package.
- Shared assets are served under `/DesktopModules/CommonSalesOrder/`.
- The public client declares an AngularJS module named `purchaseOrderApp` and a `mainController`.
- The shared controller contains paginated-table query state with a default page size of 10 and a 500 millisecond filter debounce.
- Shared dialogs use Angular Material and load HTML templates from module-relative URLs.
- Authentication uses a server-rendered POST form with anti-forgery and Web Forms state fields.
- Session-related cookies observed before login use `Secure`, `HttpOnly`, and `SameSite=Lax`.
- Observed response headers include HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, an older XSS protection header, a feature policy, and a content security policy.
- The public page declares `NOINDEX, NOFOLLOW`.

### Important limitations

- Names such as `CommonSalesOrder` and `purchaseOrderApp` may represent shared portal infrastructure. They do not prove that Deal Registration uses the same database tables or lifecycle as purchase orders.
- Public JavaScript names and HTTP forms do not reveal Canon's database schema. Field names observed later in requests may indicate API contracts, but internal column names must still be described as inferred unless independently confirmed.

## Authenticated workflow test plan

Use a unique marker in every test record, for example `DBGI-RESEARCH-20261020`, so cleanup and screenshots are unambiguous.

### 1. Landing page and record list

Record:

- Page title and navigation path
- Available tabs or record categories
- Table columns and default sort order
- Search fields, filters, pagination, and page-size choices
- Empty-state behavior
- Create, view, edit, copy, cancel, submit, and delete actions
- Whether users see only their company records
- Whether any ranking, duplicate warning, or competing-registration indicator is shown

### 2. Create form

For every visible field, capture:

- Exact label
- Required or optional state
- Control type
- Allowed values or lookup source
- Maximum length or format restriction
- Default value
- Conditional visibility
- Help text
- Client validation message
- Server validation message

Likely business areas to check, without assuming they exist, include partner identity, End-user identity, project details, bid and delivery dates, contact information, products, quantities, pricing, competitors, justification, supporting evidence, and attachments.

### 3. Save modes and lifecycle

Test each available action separately:

- Save draft
- Submit
- Edit before review
- Edit after submission
- Withdraw or cancel
- Resubmit after requested changes
- Delete
- Copy or duplicate

For every action, record the status before and after, confirmation text, actor restrictions, required rationale, notification behavior, timestamps, and whether the action is reversible.

### 4. Status catalog

Build the verified status table only from observed records:

| Status | How entered | Allowed next actions | Editable fields | Terminal | Notes |
| --- | --- | --- | --- | --- | --- |
| Pending authenticated testing | | | | | |

Check whether display labels differ from request values and whether status history is visible.

### 5. Edit and concurrency behavior

Open the same synthetic record in two tabs and determine:

- Whether the second save overwrites the first
- Whether a version conflict is reported
- Whether the portal warns about stale data
- Whether edits create history entries
- Whether submitted or approved records become read-only

### 6. Duplicate and matching behavior

Create controlled variations using the same synthetic End-user and project:

- Exact same name, address, dates, and products
- Address abbreviation changes
- Same project with a different product
- Same End-user with a different project
- Same opportunity submitted by another authorized test company, if available

Record whether Canon blocks, warns, groups, ranks, or allows each variation. Do not infer matching rules from a single result.

### 7. Product and pricing behavior

Determine:

- Whether products come from a controlled catalog
- Whether product families and models are separate
- Whether multiple products are supported
- Quantity and currency precision
- Requested price, standard price, discount, and approval fields
- Whether totals are calculated automatically
- Whether non-catalog products are permitted
- Whether competitor brand, model, price, and remarks are captured

### 8. Evidence and attachments

Record allowed file types, size limits, count limits, description fields, upload timing, replacement and deletion rules, download authorization, and whether evidence becomes immutable after review.

Use only harmless synthetic files. Do not upload confidential, personal, or third-party bid information.

### 9. Notifications and audit history

Observe in-app and email notifications for create, submit, edit, review, approval, rejection, and deletion. Record whether an activity history exposes actor, action, timestamp, prior value, new value, and rationale.

### 10. Cleanup

- Search for the unique test marker.
- Delete records when the portal permits deletion.
- If deletion is unavailable, cancel or archive them and record the final status.
- Confirm that no active synthetic registration remains.
- Record test identifiers without storing authentication secrets.

## Data dictionary template

The authenticated pass should populate this table from observed form controls and request payloads:

| UI label | Request field | Type | Required | Validation | Lookup/source | DBGI equivalent | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Username | Not inspected | Text | Yes | Not inspected | Partner account | User.username | Observed |
| Password | Not inspected | Password | Yes | Not inspected | Partner account | Authentication only | Observed |

Internal database column names must not be asserted unless Canon exposes an official schema. Request and response names should be documented as API fields, not database fields.

## Initial lessons for DBGI

### Recommendations

- Preserve the intended destination through login, as Canon does with `returnurl`.
- Keep the DBGI data dictionary explicit and version controlled rather than relying on UI labels alone.
- Test lifecycle permissions using create, edit, review, resubmit, and cleanup scenarios, not screenshots alone.
- Maintain a visible activity history for consequential changes.
- Keep synthetic competitive-analysis data clearly labeled and removable.
- Treat Canon behavior as a product reference, not automatically as the correct DBGI policy.
- Prefer DBGI's modern React, Django Ninja, and PostgreSQL architecture over copying the legacy DNN and Web Forms implementation.

## Evidence sources

- `https://partner.canon.com.ph/Deal-Registration`, accessed 2026-10-20
- `https://partner.canon.com.ph/Login?returnurl=%2fDeal-Registration`, accessed 2026-10-20
- Public portal assets under `/DesktopModules/CommonSalesOrder/`, accessed 2026-10-20
- Public response headers and HTML returned without authentication, inspected 2026-10-20

## Authenticated test completion

The authenticated pass was completed with an authorized partner account. One synthetic registration was created, edited, inspected, and deleted. Credentials and authentication artifacts were not stored. The companion findings document records the results and remaining limitations.
