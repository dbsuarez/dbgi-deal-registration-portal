# DBGI Portal Rules and How It Works

**As of:** 2026-11-05  
**Purpose:** the single reference for how the DBGI Project Registration Portal works and the business rules behind
it. Write help pages, tutorials, guides, and walkthroughs from this file, and update it whenever a rule changes.

Every rule has a status:

- **Live:** the portal does this today.
- **Decided:** DBGI decided it on 2026-10-30, but it is not built yet. Do not describe it as available.
- **Open:** still undecided.

Decision codes (A1, B2, ...) refer to [DECISIONS_TO_MAKE_2026-10-28.md](DECISIONS_TO_MAKE_2026-10-28.md); the
answers are in [DECISION_RESPONSES_2026-10-30.md](DECISION_RESPONSES_2026-10-30.md).

---

## 1. Who uses the portal

| Role                   | Who                                                        | What they can do                                                                                                                  |
| ---------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Company user (partner) | Staff of a dealer company                                  | Register and edit their company's deals, withdraw them, report outcomes, ask for repeat orders, see their own rank and prices    |
| DBGI administrator     | DBGI staff (superusers, or staff with the DBGI admin role) | Review and match registrations, decide prices and repeat orders, merge and split, verify end-users, confirm outcomes, run the dashboard |

- **Live:** each company sees only its own registrations, rankings, and prices. This is enforced by the server,
  not just hidden on screen.
- **Live:** all DBGI administrators can do everything; there are no separate reviewer or pricing roles yet.
- **Decided (A2):** start with a pilot of 2 to 3 trusted partners and one DBGI reviewer.
- **Live:** DBGI has no earlier deal registration system or existing deals. Everything starts in the portal.

## 2. The deal journey at a glance

1. A partner **registers a deal**: the end-user (government buyer), the products and requested prices, the
   competitor, and evidence.
2. DBGI **reviews** it: starts the review, then confirms it belongs to a project (matching), requests changes, or
   rejects it.
3. A confirmed registration is **Registered** and gets a **rank** among the companies on the same project.
4. DBGI **decides the prices**, per product category, with a validity date.
5. The partner can **renew** an approved price, ask for a **repeat order**, **report the project outcome**, or
   **withdraw** the deal.
6. Notifications keep both sides informed at each step.

## 3. Registering a deal

- **Live:** contact details are prefilled from the user's profile.
- **Live:** the end-user is chosen from a DBGI-maintained directory. A partner can propose a new end-user; it is
  marked pending until DBGI verifies it. Duplicate end-users are refused.
- **Live:** competitor items record the competitor brand and model; known brands are suggested, and aliases resolve
  (for example "Hewlett Packard" becomes HP).
- **Live:** products are chosen from the catalog, or typed in as a non-catalog product. Each has a quantity and a
  requested unit price. The catalog list price is captured when the deal is submitted, and the discount and line
  total are calculated.
- **Live:** each line total is rounded to 2 decimals (C3 keeps this).
- **Live:** screens call this section "Attachment" (it was "Evidence" until 2026-10-30).
- **Live:** evidence needs a description and a confirmation that the partner may share it; files are private and
  checked on upload.
- **Live:** the portal records the **submission time on the server**. That time decides the ranking and cannot be
  changed by later edits or by dates the user types in.
- **Live:** if two people edit the same registration at once, the second save is refused with a "refresh first"
  message instead of overwriting.

## 4. Registration statuses

| Status                     | Meaning                                                      | Next                                   |
| -------------------------- | ------------------------------------------------------------ | -------------------------------------- |
| Submitted                  | DBGI received it                                             | DBGI starts the review                 |
| Under review               | A DBGI administrator is reviewing it                         | Confirm, request changes, or reject    |
| Returned for changes       | DBGI needs corrections; the instructions are in the Activity | The partner edits and saves            |
| Resubmitted                | The partner saved the corrections                            | DBGI reviews again                     |
| Registered                 | DBGI confirmed it belongs to a project; it is ranked         | Pricing, outcome report, or withdrawal |
| Review required after edit | The partner edited a Registered deal                         | DBGI reviews again; the rank is kept   |
| Rejected                   | DBGI rejected it; the reason is in the Activity              | Final                                  |
| Withdrawn                  | The partner withdrew it                                      | Final                                  |

- **Live:** a registration shows three separate badges: registration status, project status, and pricing status.
- **Live (2026-11-05):** a deal stays Registered after its price is approved, and its Pricing label shows the approval.
  The old registration status "Approved" was removed, because nothing used it and it took deals out of the ranking.
- **Live (A4):** the status DBGI uses to send a registration back is called "Returned for changes" (it was
  "Changes requested"). The pricing status "Changes requested" keeps its name.

## 5. Editing a registration

- **Live:** partners can edit their registration at any time until it is withdrawn.
- **Live:** editing a "Returned for changes" registration makes it "Resubmitted".
- **Live:** a **material** edit to a Registered registration makes it "Review required after edit". It keeps its
  original submission time and rank.
- **Live:** products, quantities, and requested prices lock once DBGI starts the pricing review, and DBGI must
  request changes first. Administrative corrections stay possible.
- **Live:** evidence locks while the registration is under review and after a final decision (rejected or
  withdrawn), so it cannot change after DBGI relied on it.
- **Live (B1):** every edit is classified field by field, not by judgment:
  - **Administrative** (no DBGI review, status and rank unchanged, recorded in the Activity): contact person,
    designation, email, and number; competitor remarks; product justifications; and changes only in capitals,
    punctuation, or spacing in the project title or attachment description.
  - **Material** (DBGI review required, and the Activity lists what changed): End-user, project title, bid and
    delivery dates, attachment description and link, competitor brand, item, or bid price, and products,
    quantities, or requested prices, or a repricing request.
- **Live:** saving a "Returned for changes" registration always returns it to DBGI, even for an administrative
  correction.
- **Live:** adding, replacing, or removing attachment files never changes a price or status, and is always recorded
  in the Activity. Files stay locked during review and after a decision.
- **Live:** on a registration DBGI already confirmed (Registered), a file change also **alerts DBGI**: the
  registration is flagged for review, and DBGI gets a notice and an email. This is on by default. A superuser can
  turn it off in Django Admin, under Portal settings ("Alert DBGI when attachment files change on a registered
  deal").
- **Not yet confirmed:** the rules in this section and the repricing rules in section 11 still need the head's
  confirmation; see section 16.

## 6. DBGI review and matching

- **Live:** DBGI's review steps are: start review, then confirm the match, request changes, or reject. Each
  step needs a written reason. The partner can read the change instructions and the rejection reason in the
  Activity. The reasons for starting a review and for confirming a match are for DBGI only; the partner just sees
  that the match was confirmed.
- **Live:** to confirm a match, DBGI links the registration to an existing project scope (the whole project or a
  specific lot) or creates a new project.
- **Live:** the portal suggests matches and explains why (supporting and conflicting factors). It matches
  automatically only when it is safe; otherwise a person decides. A notice tells the partner when the system made
  the latest match.
- **Live (B3):** DBGI decides merges and splits case by case, with a written reason. Every merge and split is kept
  permanently (Administration, Merges and splits). Companies read a plain notice; the reason is for DBGI only.
  - **Merge:** on the Rankings page, **Merge** moves a project's open deals into another project, when DBGI learns they
    are the same tender. A preview shows the new order, by original submission time, with each company once. DBGI can
    change that order for this case. The old project closes. This cannot be undone.
  - **Split:** on a deal linked to a project, **Split deal** moves some products to a new deal on another lot, or a new
    lot, when one deal covers separate lots. The new deal has the same company and the original submission time. At
    least one product stays. Repeat orders that are still waiting must be decided first.
  - In both, DBGI chooses to keep decided prices or send them back for review. Original submission times never change.

## 7. Ranking

- **Live:** companies on the same project scope are ranked by their **first eligible submission time**, recorded by
  the server. Only Registered registrations are ranked, and each company counts once per scope.
- **Live:** a vague first claim cannot gain an earlier place later by adding details.
- **Live (common rule, 2026-11-05):** rank 1 gets the best price, and every other company on the project gets the same
  price as each other. DBGI still types each price by hand. The price form (Administration, Price approvals) shows the
  deal's rank and the other approved prices for the project. When DBGI saves a price that breaks this rule, the portal
  shows a warning but still saves it, so DBGI can decide an exception. If rank 1 is tied, it asks DBGI to decide the tie.
- **Live:** a partner sees only its own rank; DBGI sees the full ranking.
- **Live (B5):** exact ties (the same submission time) share a rank and show as tied until DBGI decides. On the
  Rankings page, DBGI uses **Decide tie** to set the order, with a reason. Later places do not move: a tie for 1st
  becomes 1 and 2, and the next company stays 3rd.
- **Live:** companies see only their own new rank and a notice. The reason is for DBGI only, because it may name
  another company. A decision can be changed by adding a new one, and every decision stays on record. If a company
  joins the tie later, the tie reopens; if one leaves, the decision still applies to the rest.
- **Live:** a withdrawn registration leaves the ranking.

## 8. Projects and outcomes

- **Live:** a project's status is Upcoming, Active, Won, Lost, Cancelled, or On hold.
- **Live:** DBGI administrators can set the project status with a reason; it is recorded on every linked
  registration.
- **Live (B4):** on a registration DBGI linked to a project that is still Upcoming, Active, or On hold, the partner
  can **report the outcome**: Won, Lost, or Cancelled, with a note (for example the notice of award received).
  - Only one report per registration can wait for DBGI at a time.
  - DBGI administrators get an in-portal notice and either **confirm** it (the project status changes for every
    linked registration) or **do not accept** it, with a note either way.
  - The partner is notified of the decision and sees it under "Project outcome reports". After a declined report,
    the partner can report again.

## 9. Withdrawal

- **Live (B2):** a partner can withdraw its own registration at any time before it is rejected.
  - A short reason (at least 5 characters) is required.
  - Withdrawal is **instant and final**: no DBGI confirmation and no restore.
  - The registration leaves the ranking, can no longer be edited, reviewed, or priced, and leaves DBGI's pricing
    queue.
  - Every DBGI administrator gets an in-portal notice with the company, the registration, and the reason.
- If the opportunity comes back, the partner registers a new deal.

## 10. 60-day limits

All counts are calendar days, starting from the server's recorded time.

- **Live (B6):** a registration DBGI has not confirmed (still Submitted, Under review, Returned for changes, or
  Resubmitted):
  - Day 53: the partner gets a reminder that 7 days are left.
  - Day 60: it goes back to DBGI's review queue with an Activity entry, and DBGI administrators get a notice.
  - It is never rejected automatically.
- **Live (B7):** when DBGI sets a project to **On hold** (postponed, or waiting for a reposted tender):
  - Its linked registrations keep their place for 60 days.
  - Day 53: the partners get a reminder; day 60: the registrations go back to DBGI review.
  - Setting the project to any other status ends the hold; a new hold starts a new 60 days.
- **Live:** these rules run through a daily job (`python manage.py process_deadlines`). **It must be scheduled once
  a day on the server** (cron or Task Scheduler; see the infrastructure proposal, section 8). Until it is
  scheduled, no reminders are sent and nothing returns to review.

## 11. Pricing

- **Live:** DBGI decides prices per **product category** of each registration, with item-level approved prices.
- **Live:** a category's pricing status is Pending, Changes requested, Partially approved, Approved, Rejected, or
  Expired. The registration shows one overall pricing badge.
- **Live:** a requested price is a proposal, never an approved price.
- **Live:** DBGI types the validity date when approving. After that date the price shows as Expired automatically.
- **Live (C1):** if DBGI leaves the validity date empty when approving, it is set to **90 days** from today. This
  also applies when DBGI approves in Django Admin, which is where prices are decided today. A price on a withdrawn
  deal cannot be decided there.
- **Live (C1):** the company gets a reminder **14 days** before an approved price expires (sent by the daily
  `process_deadlines` job; a new date or an approved renewal allows a new reminder).
- **Live:** a partner can request a renewal of an approved or partly approved price, one request at a time. If DBGI
  approves, the validity is extended by **30 days**, counted from the current expiry date, or from today if it has
  already expired. The partner asks with the **Request renewal** button on the deal page. DBGI answers on the same
  page with **Approve** or **Decline** and a reason, and the company is told the result. A withdrawn deal cannot be
  renewed.
- **Live (C2):** all prices are **VAT-inclusive**. Each list price records this, and the deal screens say so.
- **Live (A3):** list prices have a **history**. DBGI changes a price by adding a new record with its amount, start
  date, and reason (Django Admin, Products). A saved price can never be edited or deleted, and a price cannot start
  in the past; a future start date schedules the change.
- **Live:** each product line keeps the list price it captured, linked to the exact price record, and shows its
  price basis and capture date. **An edit does not reprice a deal unless it changes what is priced:**
  - Administrative corrections, and End-user, date, or attachment changes: keep the captured price.
  - Quantity change: keep the captured unit price; the total is recalculated.
  - Product added or changed: only that line captures the current price ("Repriced: product changed").
  - The company ticks the repricing box when editing: every catalog line captures the current price, and DBGI
    reviews it ("Repriced: requested by the company").
  - DBGI uses **Apply current list prices**, with a reason ("Repriced: DBGI decision"). The company is notified.
  - Repricing is not available once pricing review has started.
- **Live (C4):** a partner can request a product that is not in the catalog. It gets **no price review until DBGI
  adds it to the catalog**. On the registration, DBGI uses **Add to catalog** to create a new product with its first
  price or link an existing one, with a reason. The line then captures the list price, its category's price review
  opens, and the partner is notified. If that category's prices were already decided, DBGI must request changes on
  them first.
- **Live (C5 keeps this):** partners see list prices and their own approved prices, never other companies' prices.
- **Decided (A3):** the launch waits for price history (now built) as well as withdrawal (built).

## 12. Repeat orders

- **Live (D1):** a repeat order can use the approved special price only for the **same end-user**, with the agency's
  **NOA** (Notice of Award) and **NTP** (Notice to Proceed) stating it is a repeat order. Otherwise DBGI declines it and
  the partner registers a new deal. Plain-language explanation:
  [REPEAT_ORDERS_EXPLAINED.md](REPEAT_ORDERS_EXPLAINED.md).
- **Live:** on the deal page, the partner uses **Request repeat order**: quantities, both letters, and a confirmation
  that they are from the deal's end-user and say it is a repeat order. A person at DBGI reads the letters, because the
  portal cannot read them. DBGI gets a notice and an email, then uses **Accept** or **Decline** with a reason, which the
  partner can read.
- **Live:** it needs a price that is still valid, on a deal DBGI confirmed. If the price has ended, it must be renewed
  first. There is no limit on the number or quantity of repeat orders until the price ends. Each repeat order keeps the
  price it asked for, even if the deal's price changes later.

## 13. Notifications

- **Live:** the in-portal notification is the official record; email is only a copy.
- **Live:** DBGI turns email on or off per event type and edits the email templates, with previews, delivery
  tracking, and retries.
- **Live:** company notifications (submission confirmed, review decisions, price decisions, outcome decisions,
  60-day reminders) appear in the portal for **every active user of the company**.
- **Live (D2):** of those users, only the **person who submitted** the registration gets the email.
- **Live (D2):** DBGI administrators get a portal notice **and an email** when something needs their action: a new
  registration, corrections submitted, an edit after the registration was confirmed, a project outcome report, a
  60-day limit reached, a price renewal request, or a repeat order request.
- **Live:** a withdrawal only informs DBGI, so it is a portal notice without email.
- **Live:** each email still needs its event type switched on in the notification settings. The DBGI action events
  start switched on; DBGI can turn any of them off.
- **Live:** emails never contain competitor details, private evidence, or detailed pricing.

## 14. Dates, times, and working days

- **Live:** the portal uses Philippine time (Asia/Manila).
- **Live:** dates are shown as YYYY-MM-DD, and times as YYYY-MM-DD HH:mm.
- **Live:** validity periods and limits (30, 60, and 90 days) count calendar days.
- **Live (D4):** working days count Monday to Friday, excluding Philippine public holidays, with a 5:00 PM cutoff. After
  the cutoff, or on a day off, counting starts from the next working day. The only use today is the planning notice
  when asking for a price renewal or a repeat order: "allow at least one working day, up to YYYY-MM-DD". It is not a
  promise that DBGI will answer by then.
- **Live:** the portal comes with the nationwide holidays through 2027: regular holidays and special non-working
  days, from Proclamation No. 1006 (2026) and No. 1427 (2027). DBGI adds local holidays, Eid'l Fitr and Eid'l Adha
  (proclaimed separately each year), any extra declared holidays, and each new year's list in Administration, under
  Public holidays.

## 15. Records and operations

- **Live:** every change is recorded in the registration's Activity: who, when, what changed, and why.
- **Live:** DBGI's operations dashboard has queues for review, pricing, end-user verification, failed emails, and
  prices nearing expiry.
- **Live (2026-11-10):** a superuser can take a snapshot of all portal data on a test server (debug mode only), restore
  it later, and download it as a backup file or upload one. On any server, the `backup_portal` and `restore_portal`
  commands do the same from the command line.
- **Decided (D3):** keep records for 5 years, back up daily, and recover within one working day. To be set up with
  the production server.

## 16. Waiting for confirmation from the head of pricing and business development

**These rules are already working in the portal, but the head has not seen them.** They were supplied on 2026-11-04,
after the head's follow-up. The form for this is "Portal Rules to Confirm" in `docs/guides/Decision Questions`. Ask
about each one, then record the answer in
[DECISION_RESPONSES_2026-10-30.md](DECISION_RESPONSES_2026-10-30.md) and change the portal if the answer differs.

| Question to ask                                                                      | What the portal does now                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Can partners fix contact details without DBGI checking?                              | Yes: contact details, competitor remarks, product justifications, and changes only in capitals, punctuation, or spacing need no review. Status and rank stay the same, and the change is recorded.                                                                                     |
| Can they do that even after the pricing review has started?                          | Yes. Products, quantities, and requested prices stay locked.                                                                                                                                                                                                                           |
| Which changes must DBGI check?                                                       | End-user, project title, bid and delivery dates, attachment description and link, competitor brand, item, or bid price, products, quantities, requested prices, and repricing requests.                                                                                                |
| Should DBGI be alerted when a partner changes attachment files on a Registered deal? | Yes, by default: the deal is flagged for review and DBGI gets a notice and an email. A superuser can turn this off in Portal settings; then the change only shows in the Activity. On deals not yet confirmed there is no separate alert, because DBGI sees the files when it reviews. |
| Should editing a deal change its price?                                              | No, unless the edit changes what is priced. Unchanged lines keep the captured price.                                                                                                                                                                                                   |
| What if only the quantity changes?                                                   | The unit price stays; the total is recalculated. DBGI reviews the change.                                                                                                                                                                                                              |
| What if a product is added or changed?                                               | Only that line takes the current price.                                                                                                                                                                                                                                                |
| What if the End-user or dates change?                                                | The price stays, and DBGI reviews the change and can apply current prices.                                                                                                                                                                                                             |
| Can a partner ask for the current price?                                             | Yes, by ticking a box when editing. All catalog lines take the current price, and DBGI reviews it.                                                                                                                                                                                     |
| Can DBGI apply the current price itself?                                             | Yes, with a reason, until the pricing review starts. The partner is notified.                                                                                                                                                                                                          |

Also worth confirming, because these details were chosen while building his decisions:

| Question to ask                                                                                              | What the portal does now                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Which deals does the 60-day limit cover?                                                                     | Deals DBGI has not confirmed, counted from submission.                                                                                                                     |
| What counts as a postponed or reposted tender?                                                               | DBGI sets the project to On hold, which starts the 60 days.                                                                                                                |
| Which events email DBGI reviewers?                                                                           | A new registration, corrections submitted, an edit after registration, an outcome report, a 60-day limit, and a price renewal request. Withdrawals are in the portal only. |
| When DBGI decides a tie, should it set a final order, or only note the decision while the rank stays shared? | It sets a final order, so the companies get different ranks.                                                                                                               |
| Can a typed-in product join a category whose prices are already decided?                                     | Not until DBGI requests changes on that category.                                                                                                                          |

Also worth confirming, because these details were chosen while building repeat orders, merges, and splits:

| Question to ask                                                  | What the portal does now                                                                                                  |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Can a partner request a repeat order after the price has ended?  | No. The price must be renewed first.                                                                                      |
| Is there a limit on repeat orders?                               | No limit on the number or quantity until the price ends.                                                                  |
| When two projects merge, who gets first place?                   | By original submission time, with each company once, unless DBGI changes the order for that case.                         |
| What happens to decided prices in a merge or split?              | DBGI chooses each time: keep them, or send them back for review.                                                          |
| When a deal is split, does the new deal keep its place in line?  | Yes. It keeps the same company and the original submission time.                                                          |

## 17. Keeping this file current

- When a feature ships, change its rule from **Decided** to **Live** and remove "not built yet".
- When DBGI decides an open question, record it in the decision responses file first, then here.
- Help pages, guides, and the walkthrough deck must not describe a **Decided** rule as available.
