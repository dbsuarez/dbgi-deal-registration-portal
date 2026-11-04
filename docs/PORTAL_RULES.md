# DBGI Portal Rules and How It Works

**As of:** 2026-10-30  
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

| Role                   | Who                                                        | What they can do                                                                                                   |
| ---------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Company user (partner) | Staff of a dealer company                                  | Register and edit their company's deals, withdraw them, report outcomes, see their own ranking and approved prices |
| DBGI administrator     | DBGI staff (superusers, or staff with the DBGI admin role) | Review and match registrations, decide prices, verify end-users, confirm outcomes, run the operations dashboard    |

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
5. The partner can **renew** an approved price, **report the project outcome**, or **withdraw** the deal.
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
| Approved                   | DBGI approved the registration                               | Outcome report or withdrawal           |
| Rejected                   | DBGI rejected it; the reason is in the Activity              | Final                                  |
| Withdrawn                  | The partner withdrew it                                      | Final                                  |

- **Live:** a registration shows three separate badges: registration status, project status, and pricing status.
- **Live (A4):** the status DBGI uses to send a registration back is called "Returned for changes" (it was
  "Changes requested"). The pricing status "Changes requested" keeps its name.

## 5. Editing a registration

- **Live:** partners can edit their registration at any time until it is withdrawn.
- **Live:** editing a "Returned for changes" registration makes it "Resubmitted".
- **Live:** a **material** edit to a Registered registration makes it "Review required after edit". It keeps its
  original submission time and rank.
- **Live:** products, quantities, and requested prices lock once DBGI starts the pricing review, and DBGI must
  request changes first. Administrative corrections stay possible.
- **Live:** evidence locks while the registration is under review and after a decision (approved, rejected, or
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
- **Open:** whether changing attachment files is administrative. Today it never changes prices or status, but it
  flags the registration for DBGI to look at.

## 6. DBGI review and matching

- **Live:** DBGI's review steps are: start review, then confirm the match, request changes, or reject. Each
  decision needs a written reason, which the partner can read in the Activity.
- **Live:** to confirm a match, DBGI links the registration to an existing project scope (the whole project or a
  specific lot) or creates a new project.
- **Live:** the portal suggests matches and explains why (supporting and conflicting factors). It matches
  automatically only when it is safe; otherwise a person decides. A notice tells the partner when the system made
  the latest match.
- **Decided (B3):** DBGI decides merges and splits case by case, with a written reason. Not built yet.

## 7. Ranking

- **Live:** companies on the same project scope are ranked by their **first eligible submission time**, recorded by
  the server. Only Registered registrations are ranked, and each company counts once per scope.
- **Live:** a vague first claim cannot gain an earlier place later by adding details.
- **Live:** a partner sees only its own rank; DBGI sees the full ranking.
- **Live:** exact ties (the same submission time) share a rank and are marked as tied.
- **Decided (B5):** for a tie, DBGI decides. A place to record that decision is not built yet.
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
- **Live (C1):** if DBGI leaves the validity date empty when approving, it is set to **90 days** from today.
- **Live (C1):** the company gets a reminder **14 days** before an approved price expires (sent by the daily
  `process_deadlines` job; a new date or an approved renewal allows a new reminder).
- **Live:** a partner can request a renewal of an approved or partly approved price, one request at a time. If DBGI
  approves, the validity is extended by **30 days**, counted from the current expiry date, or from today if it has
  already expired.
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
- **Live:** non-catalog products can be requested but get **no price review**.
- **Decided (C4):** DBGI adds a non-catalog product to the catalog first, then reviews its price. Not built yet.
- **Live (C5 keeps this):** partners see list prices and their own approved prices, never other companies' prices.
- **Decided (A3):** the launch waits for price history (now built) as well as withdrawal (built).

## 12. Repeat orders

- **Decided (D1), not built yet:** a repeat order can use the approved special price only for the **same end-user**,
  with the agency's **NOA** (Notice of Award) and **NTP** (Notice to Proceed) stating it is a repeat order.
  Otherwise DBGI declines it and the partner registers a new deal. Plain-language explanation:
  [REPEAT_ORDERS_EXPLAINED.md](REPEAT_ORDERS_EXPLAINED.md).

## 13. Notifications

- **Live:** the in-portal notification is the official record; email is only a copy.
- **Live:** DBGI turns email on or off per event type and edits the email templates, with previews, delivery
  tracking, and retries.
- **Live:** company notifications (submission confirmed, review decisions, price decisions, outcome decisions,
  60-day reminders) appear in the portal for **every active user of the company**.
- **Live (D2):** of those users, only the **person who submitted** the registration gets the email.
- **Live (D2):** DBGI administrators get a portal notice **and an email** when something needs their action: a new
  registration, corrections submitted, an edit after the registration was confirmed, a project outcome report, a
  60-day limit reached, or a price renewal request.
- **Live:** a withdrawal only informs DBGI, so it is a portal notice without email.
- **Live:** each email still needs its event type switched on in the notification settings. The DBGI action events
  start switched on; DBGI can turn any of them off.
- **Live:** emails never contain competitor details, private evidence, or detailed pricing.

## 14. Dates, times, and working days

- **Live:** the portal uses Philippine time (Asia/Manila).
- **Live:** dates are shown as YYYY-MM-DD, and times as YYYY-MM-DD HH:mm.
- **Live:** validity periods and limits (30, 60, and 90 days) count calendar days.
- **Decided (D4):** deadlines stated in working days count Monday to Friday, excluding Philippine public holidays,
  with a 5:00 PM cutoff. Not built yet; no current feature uses working days.

## 15. Records and operations

- **Live:** every change is recorded in the registration's Activity: who, when, what changed, and why.
- **Live:** DBGI's operations dashboard has queues for review, pricing, end-user verification, failed emails, and
  prices nearing expiry.
- **Decided (D3):** keep records for 5 years, back up daily, and recover within one working day. To be set up with
  the production server.

## 16. Still open

| Code | Question                                                        |
| ---- | --------------------------------------------------------------- |
| Open | Whether changing attachment files is administrative or material |

## 17. Keeping this file current

- When a feature ships, change its rule from **Decided** to **Live** and remove "not built yet".
- When DBGI decides an open question, record it in the decision responses file first, then here.
- Help pages, guides, and the walkthrough deck must not describe a **Decided** rule as available.
