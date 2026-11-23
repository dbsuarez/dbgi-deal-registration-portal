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

| Role                   | Who                                                        | What they can do                                                                                                                        |
| ---------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Company user (partner) | Staff of a dealer company                                  | Register and edit their company's deals, close them, report outcomes, ask for repeat orders, see their own rank and prices              |
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
   **close** the deal.
6. Notifications keep both sides informed at each step.

## 3. Registering a deal

- **Live:** contact details are prefilled from the user's profile.
- **Live:** the end-user is chosen from a DBGI-maintained directory. A partner can propose a new end-user; it is
  marked pending until DBGI verifies it. Duplicate end-users are refused.
- **Live (setting, 2026-11-23):** a new end-user's street address is optional unless a superuser switches on "Street
  address is required for a new end-user" in Portal settings, under Forms (default: off).
- **Live:** competitor items record the competitor brand and model; known brands are suggested, and aliases resolve
  (for example "Hewlett Packard" becomes HP).
- **Live (setting, 2026-11-23):** competitor items are optional unless a superuser switches on "Competitor items are
  required" in Portal settings, under Forms (default: off).
- **Live:** products are chosen from the catalog, or typed in as a non-catalog product. Each has a quantity and a
  requested unit price. The catalog list price is captured when the deal is submitted, and the discount and line
  total are calculated.
- **Live (setting, 2026-11-23):** a product DBGI does not list (typed in as Not in catalog) is only worth sourcing from
  the supplier for a big order: its quantity times requested price must be at least **1,000,000**, or the
  registration is refused with a clear message. A superuser changes the amount in Portal settings, under Forms
  (0 turns the rule off).
- **Live (2026-11-23):** DBGI checks a typed-in product with the supplier. If it can be sourced, DBGI uses **Add to
  catalog** (section 11). If not, DBGI uses **Can't supply** on that product line, with a reason: the line is marked
  **Not available**, left out of pricing and the catalog, and the company gets a message and reads the reason. Only
  that line stops; if it was the deal's only product, DBGI rejects the deal as usual.
- **Live:** each line total is rounded to 2 decimals (C3 keeps this).
- **Live:** screens call this section "Attachment" (it was "Evidence" until 2026-10-30).
- **Live:** evidence needs a description and a confirmation that the partner may share it; files are private and
  checked on upload.
- **Live:** the portal records the **submission time on the server**. That time decides the ranking and cannot be
  changed by later edits or by dates the user types in.
- **Live:** if two people edit the same registration at once, the second save is refused with a "refresh first"
  message instead of overwriting.

## 4. Registration statuses

| Status                     | Meaning                                                      | Next                                 |
| -------------------------- | ------------------------------------------------------------ | ------------------------------------ |
| Submitted                  | DBGI received it                                             | DBGI starts the review               |
| Under review               | A DBGI administrator is reviewing it                         | Confirm, request changes, or reject  |
| Returned for changes       | DBGI needs corrections; the instructions are in the Activity | The partner edits and saves          |
| Resubmitted                | The partner saved the corrections                            | DBGI reviews again                   |
| Registered                 | DBGI confirmed it belongs to a project; it is ranked         | Pricing, outcome report, or closing  |
| Review required after edit | The partner edited a Registered deal                         | DBGI reviews again; the rank is kept |
| Rejected                   | DBGI rejected it; the reason is in the Activity              | Final                                |
| Cancelled                  | The company or DBGI cancelled it; the reason is in Activity  | Only DBGI can reopen it              |

- **Live:** a registration shows three separate badges: registration status, project status, and pricing status.
- **Live (2026-11-05):** a deal stays Registered after its price is approved, and its Pricing label shows the approval.
  The old registration status "Approved" was removed, because nothing used it and it took deals out of the ranking.
- **Live (A4):** the status DBGI uses to send a registration back is called "Returned for changes" (it was
  "Changes requested"). The pricing status for the same idea is called "Needs a new price" (it was "Changes
  requested", renamed 2026-11-19).

## 5. Editing a registration

- **Live:** partners can edit their registration at any time until it is closed.
- **Live:** editing a "Returned for changes" registration makes it "Resubmitted".
- **Live:** a **material** edit to a Registered registration makes it "Review required after edit". It keeps its
  original submission time and rank.
- **Live:** a category's products, quantities, and requested prices lock once DBGI decides its price.
  Administrative corrections stay possible.
- **Live (2026-11-19):** when DBGI chooses **Ask for a new price**, that category's pricing shows **Needs a new
  price**, and the company can change its products, quantities, and prices again. When the company saves, the price
  goes back to **Pending**, DBGI gets a notice and an email ("New price to decide"), and DBGI decides it again with
  Decide price. If the new price is the only material change, the deal stays Registered and keeps its rank; with other
  material changes it needs review as usual. Categories with a decided price stay locked.
- **Live:** evidence locks while the registration is under review and after a final decision (rejected or
  closed), so it cannot change after DBGI relied on it.
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
- **Live (2026-11-19):** a deal is never matched automatically to a project that is already **Won, Lost, or
  Cancelled**. The suggestion still shows that project, with the warning "This project is already Won", so DBGI does
  not create a duplicate. DBGI can still link it on purpose: closed projects are marked, for example "(Won)", in
  the list.
- **Live (2026-11-19):** a **new** deal that certainly matches a **Won** project (the same end-user name and address,
  and all the same products) is **rejected automatically** with the reason "This project was already awarded", and
  the company is told. A near match goes to DBGI with the warning instead. Lost and Cancelled projects are never
  rejected automatically, because a tender is often posted again. A deal already on the project is never rejected
  by this rule, even after an edit.
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
  price as each other. DBGI still types each price by hand, in the **Decide price** box on the deal page (Commercial approvals).
  The box shows the deal's rank and the other approved prices for the project. **Since 2026-11-23**, a price that breaks
  this rule is not saved until DBGI ticks "I confirm this exception to the rank rule", so an exception is always on
  purpose. Tied companies at rank 1 all count as rank 1: they get the same best price.
- **Live:** a partner sees only its own rank; DBGI sees the full ranking.
- **Live (head's answer, 2026-11-11):** exact ties (the same submission time) keep the same rank, shown as "Tied".
  The next company skips a place: after a tie for 1st comes 3rd. Since only rank 1 gets the best price, the number of
  the next place does not change any price.
- **Live (setting, default off):** a DBGI superuser can switch on "Let DBGI set the order of tied companies" in Portal
  settings, under Ranking. Then DBGI uses **Decide tie** on the Rankings page to set the order, with a reason that only
  DBGI can read. Tie orders saved while it was on stay on record, and apply again whenever it is switched back on.
- **Live:** a closed registration leaves the ranking until DBGI reopens it.

## 8. Projects and outcomes

- **Live:** a project's status is Upcoming, Active, Won, Lost, Cancelled, or On hold. DBGI changes it with
  **Change project status** at the top of any deal on the project; a reason is required and saved on each deal.
- **Live:** DBGI administrators can set the project status with a reason; it is recorded on every linked
  registration.
- **Live (B4):** on a registration DBGI linked to a project that is still Upcoming, Active, or On hold, the partner
  can **report the outcome**: Won, Lost, or Cancelled, with a note.
  - **Live (2026-11-19):** a project is won when the company receives the **Notice of Award (NOA)**. A Won report
    must attach the NOA file (PDF, picture, Word, or Excel); DBGI opens it before confirming. Lost and Cancelled
    reports may attach it.
  - Only one report per registration can wait for DBGI at a time.
  - DBGI administrators get an in-portal notice and either **confirm** it (the project status changes for every
    linked registration) or **do not accept** it, with a note either way.
  - The partner is notified of the decision and sees it under "Project outcome reports". After a declined report,
    the partner can report again.
- **Live (2026-11-19):** a plain "Won" on every linked deal could make a losing company think it won, so partners see:
  - **Won by your company**, when DBGI confirmed that company's Won report.
  - **Awarded to another company**, on the other companies' deals. The winner is not named.
  - **Awarded**, when DBGI set Won with Change project status, without a report saying who won.
  - DBGI still sees **Won**. DBGI's confirmation note goes only on the reporting company's deal; the others get a
    plain line in their Activity.
- **Live (2026-11-19):** after DBGI confirms a Won report:
  - Every DBGI administrator gets a reminder to issue the **manufacturer certificate** and the **dealer
    certificate** to the winner. The certificates are issued outside the portal. The reminder shows on the deal and
    on the DBGI dashboard ("Certificates to issue") until any DBGI administrator clicks **Mark certificates issued**.
    The company does not see this step.
  - The winning deal lists the other companies' deals still open on the project, each with **Close**, so DBGI can
    call each company and close its deal.

## 9. Cancelling and reopening a deal

- **Live (2026-11-19, renamed 2026-11-23):** **Cancel deal** replaced Withdraw. It was first called "Close deal",
  which could be read as "done" or "won", so the button is **Cancel deal** and the status is **Cancelled**. A deal can
  be cancelled at any time before it is rejected:
  - **The company** cancels its own deal. Every DBGI administrator gets an in-portal notice with the reason.
  - **Any DBGI administrator** cancels it for the company, usually after a phone call when another company won, with
    a note from the call. The company is told and can read the note.
  - A reason is chosen (another company won, the project was cancelled, the company stopped pursuing it, or other),
    and a note of at least 5 characters is required.
  - A cancelled deal leaves the ranking, can no longer be edited, reviewed, renewed, or priced, gets no repeat orders,
    and leaves DBGI's queues. It stays on record.
- **Live (2026-11-19):** **any DBGI administrator can reopen** a cancelled deal, with a reason (for example, the
  winner was disqualified). It returns to the status it had before it was cancelled, keeps its original submission time and
  its place in the ranking, and the company is told. Companies cannot reopen a deal.
- Deals withdrawn before 2026-11-19 became Cancelled, with the reason "Withdrawn by the company".

## 10. 60-day limits

All counts are calendar days, starting from the server's recorded time.

- **Live (2026-11-16):** the lengths below are **Portal settings** a DBGI superuser can change in Administration,
  under Time limits. The defaults are shown. Changes apply from the next daily check.
- **Live (B6):** a registration DBGI has not confirmed (still Submitted, Under review, Returned for changes, or
  Resubmitted):
  - 7 days before the limit (default day 53): the partner gets a reminder.
  - At the limit (default day 60): it goes back to DBGI's review queue with an Activity entry, and DBGI administrators
    get a notice.
  - It is never rejected automatically.
- **Live (B7):** when DBGI sets a project to **On hold** (postponed, or waiting for a reposted tender):
  - Its linked registrations keep their place for the hold limit (default 60 days).
  - The same reminder comes first; at the limit the registrations go back to DBGI review.
  - Setting the project to any other status ends the hold; a new hold starts the count again.
- **Live:** these rules run through a daily job (`python manage.py process_deadlines`), scheduled on the test server
  since 2026-11-19 at 06:00 Asia/Manila (`deploy/cron.d/dbgi-portal`; see the infrastructure proposal, section 8). Any
  new server needs the same schedule; without it, no reminders are sent and nothing returns to review.

## 11. Pricing

- **Live:** DBGI decides prices per **product category** of each registration, with item-level approved prices.
- **Live:** a category's pricing status is Pending, Needs a new price, Partially approved, Approved, Rejected, or
  Expired. The registration shows one overall pricing badge.
- **Live:** a requested price is a proposal, never an approved price.
- **Live:** DBGI types the validity date when approving. After that date the price shows as Expired automatically.
- **Live (C1):** if DBGI leaves the validity date empty when approving, it is set to **90 days** from today.
- **Live (2026-11-23):** prices are decided only with **Decide price** on the deal page. The old price page in Django
  Admin is view only, because it could not apply the rules below.
- **Live (2026-11-23), landed cost:** each product has a **landed cost** (what one unit costs DBGI once it arrives),
  kept as a dated history in Administration, Products, beside the list price. Only DBGI sees it.
  - A product with no landed cost **cannot be priced** until someone enters it.
  - **No approved price can go below the landed cost.** An admin is refused. The owner can do it only after a red
    warning and ticking "This is not a typo. I approve selling below the landed cost."
- **Live (2026-11-23), discount limit:** an admin can approve a discount of up to **5%** from the list price (a Portal
  setting, under Pricing). A bigger discount goes to the **owner**:
  - The price becomes "Waiting for owner approval". The partner still sees it as Pending, with no amount.
  - The owner (a DBGI admin with Owner switched on, in Administration, Users) gets an email and a portal message. His
    home page shows how many prices are waiting, and the top menu shows **Owner approvals (2)**.
  - The owner decides everything on that one page, without Django Admin (the Administration link is hidden for
    him): each waiting price shows the list price, landed cost, proposed price, and discount. He can change the price,
    writes a short note, and clicks **Approve** or **Decline**. A price below the landed cost needs his confirmation,
    as above. The partner is then told. The owner can also use Decide price on the deal page.
- **Live (2026-11-23), the owner's Overview:** the owner's home page is a short **Overview**, so he sees what is
  happening without reading every deal:
  - Prices waiting for his approval (only when there are any).
  - This month so far, compared with last month: new deals, projects won and their value, projects lost or
    cancelled, and the pipeline (the value of open deals). Won, lost, and cancelled count the outcome reports DBGI
    confirmed. Values use approved prices where there are any, and requested prices otherwise.
  - Bids in the next 14 days, each marked Decided or Not decided; anything stuck (a deal waiting for DBGI review
    more than 7 days, or a price waiting for him more than 2 days); the last 5 wins, with whether the certificates
    were issued; and the top 5 partners of the quarter by registered value.
  - Since 2026-11-23 it also shows: the **average discount** approved this month and last month (from the list price,
    weighted by value); the **win rate** this quarter (won out of won and lost; cancelled projects are not counted);
    **thin margins** (approved prices less than 5% above the landed cost, on open deals); and **prices ending soon**
    (approved prices ending in the next 14 days on deals whose bid date has not passed).
  - Every list shows at most 5 rows. **All deals** opens the full deal list (also at /deals/).
- **Live (setting, 2026-11-23):** every Monday at 07:00 Asia/Manila the owner gets an email with the same numbers
  (`send_owner_summary`, scheduled with the daily job in `deploy/cron.d/dbgi-portal`). A superuser can switch it off
  in Portal settings, under Pricing (default: on).
- **Live (2026-11-23), price deadline:** prices must be decided **7 days before the bid date** (a Portal setting,
  under Pricing). If a deal's price is still undecided by then, every DBGI admin gets a portal message and an email,
  once per bid date, from the daily job.
- **Live (C1):** the company gets a reminder **14 days** before an approved price expires (sent by the daily
  `process_deadlines` job; a new date or an approved renewal allows a new reminder).
- **Live:** a partner can request a renewal of an approved or partly approved price, one request at a time. If DBGI
  approves, the validity is extended by **30 days**, counted from the current expiry date, or from today if it has
  already expired. The partner asks with the **Request renewal** button on the deal page. DBGI answers on the same
  page with **Approve** or **Decline** and a reason, and the company is told the result. A closed deal cannot be
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
  opens, and the partner is notified. If that category's prices were already decided, DBGI must ask for a new price on
  them first.
- **Live (C5 keeps this):** partners see list prices and their own approved prices, never other companies' prices.
- **Decided (A3):** the launch waits for price history (now built) as well as withdrawal (built; now Close deal).

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
- **Live (head's answer, 2026-11-11):** an accepted repeat order stays valid for a set time, counted from the day DBGI
  accepts it (default 1 year). It then shows as "Accepted, now ended". The length is a Portal setting a DBGI superuser
  can change; repeat orders accepted before a change keep their end date.

## 13. Notifications

- **Live:** the in-portal notification is the official record; email is only a copy.
- **Live:** DBGI turns email on or off per event type and edits the email templates, with previews, delivery
  tracking, and retries.
- **Live:** company notifications (submission confirmed, review decisions, price decisions, outcome decisions,
  60-day reminders) appear in the portal for **every active user of the company**.
- **Live (D2):** of those users, only the **person who submitted** the registration gets the email.
- **Live (D2):** DBGI administrators get a portal notice **and an email** when something needs their action: a new
  registration, corrections submitted, an edit after the registration was confirmed, a project outcome report, a
  60-day limit reached, a price renewal request, or a repeat order request. The renewal request email can be turned
  off in Portal settings, under Emails and alerts to DBGI (default: on).
- **Live:** a company closing its own deal only informs DBGI, so it is a portal notice without email. The
  certificate reminder is also a portal notice without email; it stays on the dashboard until it is done.
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

**Answered 2026-11-11, and built 2026-11-16.** The head confirmed 16 of the 20 rules below as built. For the other four,
ties now keep the same rank, and the 60-day limit, the renewal request email, and how long an accepted repeat order
stays valid are Portal settings DBGI can change. Details are in
[DECISION_RESPONSES_2026-10-30.md](DECISION_RESPONSES_2026-10-30.md). The tables below are kept as the record of what
was asked.

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

| Question to ask                                                                                              | What the portal does now                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Which deals does the 60-day limit cover?                                                                     | Deals DBGI has not confirmed, counted from submission.                                                                                                                       |
| What counts as a postponed or reposted tender?                                                               | DBGI sets the project to On hold, which starts the 60 days.                                                                                                                  |
| Which events email DBGI reviewers?                                                                           | A new registration, corrections submitted, an edit after registration, an outcome report, a 60-day limit, and a price renewal request. Closing a deal is in the portal only. |
| When DBGI decides a tie, should it set a final order, or only note the decision while the rank stays shared? | It sets a final order, so the companies get different ranks.                                                                                                                 |
| Can a typed-in product join a category whose prices are already decided?                                     | Not until DBGI requests changes on that category.                                                                                                                            |

Also worth confirming, because these details were chosen while building repeat orders, merges, and splits:

| Question to ask                                                 | What the portal does now                                                                          |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Can a partner request a repeat order after the price has ended? | No. The price must be renewed first.                                                              |
| Is there a limit on repeat orders?                              | No limit on the number or quantity until the price ends.                                          |
| When two projects merge, who gets first place?                  | By original submission time, with each company once, unless DBGI changes the order for that case. |
| What happens to decided prices in a merge or split?             | DBGI chooses each time: keep them, or send them back for review.                                  |
| When a deal is split, does the new deal keep its place in line? | Yes. It keeps the same company and the original submission time.                                  |

## 17. Keeping this file current

- When a feature ships, change its rule from **Decided** to **Live** and remove "not built yet".
- When DBGI decides an open question, record it in the decision responses file first, then here.
- Help pages, guides, and the walkthrough deck must not describe a **Decided** rule as available.
