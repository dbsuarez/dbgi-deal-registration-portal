# Canon Deal Registration Authenticated Findings

Date observed: 2026-10-20

Reference: https://partner.canon.com.ph/Deal-Registration

This document supplements `CANON_DEAL_REGISTRATION_REVERSE_ENGINEERING_2026-10-20.md` with authenticated findings. Testing used an authorized partner account. One clearly labeled synthetic registration was created, edited, inspected, and permanently deleted. No existing registration was changed. Credentials and authentication artifacts are not recorded.

## List and status model

The registration list has separate columns for Project Status, Registration Status, and Price Approval Status. It offers project-status filters for Won, Ongoing, and Lost, plus registration-status filters for New, Preferred, Supported, Ongoing, Rejected, and Done. It also provides Show All or Show Pending, CSV export, pagination, grand total, record age, and View and Delete actions.

The synthetic record appeared with:

- Project status: blank.
- Registration status: New.
- Price approval status: Ongoing.
- Product-category approval: Pending.

The list-level price status is therefore not a direct copy of the category approval status. Its exact rollup rule could not be proven with a non-approver account.

## Entry data

Header and end-user fields:

- Partner, automatically determined and locked for a normal partner user.
- End-User Name, with suggestions.
- Status, New on creation.
- Complete Address.
- Project Opportunity Title.
- Bid Date.
- Delivery Date.
- Contact Person.
- Designation.
- Email.
- Contact Number.

At least one competitor item is required. A competitor contains brand, item name, bid price, and remarks.

At least one product is required. Products come from a searchable catalog and contain item code, item name, category, quantity, SRP, requested price, calculated discount percentage, total price, and remarks or justification. In the live test, selecting a product supplied its category and SRP, quantity defaulted to 1, requested price defaulted to SRP, discount defaulted to 0%, and total was quantity multiplied by requested price.

The document section accepts multiple files and displays file name, size, and upload date.

## Validation observations

The authenticated client requires end-user name, address, project title, bid date, delivery date, contact name, contact number, email, at least one competitor, and at least one product before enabling submission.

For a new record, bid date must be later than the current date and no later than delivery date. Delivery date must remain later than the current date. Existing records receive special handling when the original bid date has already passed.

Two client inconsistencies are worth avoiding:

- Designation is visually marked required but was absent from the observed submission predicate.
- `ExpectedPartnerBidPrice` is checked by that predicate although its visible field is commented out.

This does not prove the server accepts invalid payloads because server-side validation was not bypass-tested.

## Approval workflow

The application creates one approval row per distinct product category. Each approval contains category, status, remarks, approver, approval timestamp, and a permission flag. Approval status begins as Pending and authorized category approvers can select Approved or Rejected.

Authenticated client comments state that the registration becomes Ongoing after any category approval action. Admin or host users can mark a saved registration Done. Done is read-only. An admin can reopen Done to Ongoing. Preferred also makes partner-side fields, products, competitors, and documents read-only.

The exact transitions into Preferred, Supported, and Rejected were not tested because the supplied account was not an approver or administrator.

## History and controlled test

Saved records expose a paginated History table containing timestamp, event, details, and actor.

The controlled test used marker `DBGI-RESEARCH-20261020-01` and synthetic contact data:

1. Save created registration `REGIDC0000017` and returned to the list.
2. Opening it showed one Pending approval for product category `DR` and a Created history event.
3. Editing the project title and saving added a separate Updated event while retaining the Created event.
4. Delete showed an irreversible-action confirmation naming the end-user and project.
5. After confirmation, the marker no longer appeared in the list.

Cleanup status: complete. The synthetic record was permanently deleted.

## Implementation behavior and risks

- Registration save and document upload are separate operations. If upload fails, the record remains saved and the client returns to the list after warning the user. Our application should keep explicit staged upload and finalization semantics or otherwise represent partial success clearly.
- Delete is exposed directly in each list row. For real business data, our application should favor cancellation or archival and restrict permanent deletion to controlled administrative cleanup.
- The observed write payload does not expose an optimistic concurrency version. Our existing conflict protection is safer.
- Dates are displayed as `M/D/YYYY` and timestamps use a 12-hour clock. Our project must retain `YYYY-MM-DD` and `YYYY-MM-DD HH:mm`.
- Registration and project status both use Ongoing, which can confuse users. Our status labels and contextual help should make each axis unambiguous.
- The portal records a generic Updated event. Field-level change evidence would be more useful for sensitive changes.

## Recommended mapping to DBGI

| Canon concept | DBGI concept | Direction |
|---|---|---|
| Partner | Registering company | Keep server-enforced company membership |
| End-User | End-user organization | Use reusable End-user master data and a governed create flow |
| Project Opportunity Title | Opportunity | Keep the current Opportunity naming and lifecycle |
| Registration status | Registration lifecycle | Define explicit transitions and role permissions |
| Project status | Opportunity outcome | Keep separate from review and approval |
| Price approval status | Review decision rollup | Derive it from category decisions using a documented rule |
| Category approval | Registration review decision | Support one decision per relevant category and preserve history |
| Items | Registration items | Retain quantity, list price, requested price, discount, total, and justification |
| Competitor items | Competitor items | Retain brand, item, bid price, and remarks |
| Documents | Evidence attachments | Keep staged upload plus explicit finalize semantics |
| History | Registration events | Continue append-only actor-attributed events |

## Decisions still needed

- Whether one category rejection determines the overall result or all categories must decide.
- The exact business distinction between Supported and Preferred.
- Who can set project outcome to Ongoing, Won, or Lost.
- Whether a submitted New registration remains editable or editing is limited to explicit Draft state.
- Which documents are mandatory based on deal type, value, or requested discount.
- The retention and cancellation policy that should replace permanent deletion.

These are product-owner decisions and should not be copied from the observed portal without confirmation.

## Limitations

- The walkthrough used a normal partner account, not an approver, administrator, or host.
- Approval decisions, Done and reopen actions, CSV contents, file restrictions, cross-company authorization, and concurrent editing were not executed.
- Client behavior reveals intent but does not prove all server-side enforcement.
- Findings are a point-in-time observation and may change.
