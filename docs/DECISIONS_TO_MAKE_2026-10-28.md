# Decisions To Make Before Building More

**As of:** 2026-10-28  
**Purpose:** a plain-language question list for the people at DBGI who run deal registration, pricing, and IT.
Their answers decide what gets built next, so the portal follows the process DBGI wants instead of guesses. DBGI has no deal registration system yet; the portal will be the first.

## How to use this

These questions are sent at the end of the **Using the DBGI Portal** slide deck, one slide per question,
to the people who handle partner deals (sales or channel), pricing (finance), and IT.
The deck's walkthrough slides show the screens each question refers to.

1. Answer **Part A first**. If an answer there is a surprise, it changes the plan before anything else.
2. Answer each question with a choice letter, "keep today", or your own rule in a sentence. Skip anything outside your area.
   The easiest way is the Word **DBGI Portal Answer Form**, sent with the deck: it has a drop-down and a notes box per question.
   You can also reply by email, one line per question, for example `B2: a`.
3. Prefer paper? The printable sheet **DBGI Portal Decisions** has the same questions and ids, with tick boxes.
4. Each answer is then applied to the portal: it is recorded in the roadmap's decision register with the date and
   who answered, and becomes a build task. "Keep today" means no change is needed.

Each question has the same parts:

- **Means:** the question in plain words.
- **Today:** what the portal does now. If that already works for DBGI, the answer is simply "keep today".
- **Choices:** realistic options. The first one is the suggested starting point, not a decision.
- **Unblocks:** what can be built once it is answered.

---

## Part A. Are we building the right thing?

These check the foundation. A wrong answer here matters more than any detail below.

### A1. Is this the process DBGI wants?

- **Means:** DBGI has no deal registration system yet; the portal will be the first. It follows this process: a partner registers a deal, DBGI checks it, decides who was first, then approves a special price. Is that the process DBGI wants partners to follow?
- **Today:** the portal does exactly that loop, end to end, with notifications.
- **Ask:** Is anything in this process wrong or missing for DBGI? What would you change?
- **Unblocks:** confidence that the remaining work is on the right path.
- **Answer:**

### A2. What about deals partners already told DBGI about?

- **Means:** before the portal goes live, partners may already have told DBGI about deals by email, phone, or chat, or been promised a special price. When the portal starts, do those deals keep their place in line?
- **Today:** the portal only knows deals entered into it, and ranks them by the time they were submitted in the portal. An older deal entered after launch counts from its entry time; nobody can enter an earlier date.
- **Choices:** (a) start fresh: only deals submitted in the portal count, and partners are told the launch date in advance; (b) DBGI enters known deals at launch, with proof of the earlier date, and ranks them first; (c) partners get a short window (for example two weeks) to register existing deals, which DBGI reviews case by case.
- **Unblocks:** the launch plan, and whether the portal needs a way to enter older deals with their original date.
- **Answer:**

### A3. Who will actually use it first?

- **Means:** which DBGI staff review registrations, and which partner companies should try it first.
- **Today:** two roles exist: company user (partner staff) and DBGI administrator. All DBGI admins can do everything.
- **Choices:** (a) a small pilot with 2 to 3 trusted partners and one DBGI reviewer; (b) all partners at once.
- **Unblocks:** user accounts, training, and whether DBGI needs separate reviewer and pricing roles.
- **Answer:**

### A4. What must work on day one, and what can wait?

- **Means:** the smallest version DBGI would actually use.
- **Today:** registration, review, ranking, and price approval work. Withdrawal, merging deals, price history, and reorders do not exist yet.
- **Choices:** (a) launch with today's loop plus withdrawal; (b) wait for pricing history too; (c) wait for reorders as well.
- **Unblocks:** the launch date and what is in scope for it.
- **Answer:**

### A5. Do the words make sense to partners?

- **Means:** labels like "Registered", "Changes requested", "Review required after edit", "Opportunity scope", "Lot".
- **Today:** registration statuses are Submitted, Under review, Changes requested, Resubmitted, Registered, Review required after edit, Approved, and Rejected.
- **Ask:** Would a partner understand these labels? Which words would partners and DBGI staff expect instead?
- **Unblocks:** final screen labels and help text.
- **Answer:**

---

## Part B. Questions that block the next build (deal lifecycle)

### B1. Can partners edit a deal after submitting it?

- **Means:** once a partner submits, can they keep changing it, or only when DBGI asks?
- **Today:** partners can edit at any time. Products and prices lock once DBGI starts the price review. Editing a deal that is already Registered sends it back to DBGI ("Review required after edit"), but it keeps its original place in line.
- **Choices:** (a) keep today's rule; (b) only edit when DBGI requests changes; (c) allow small fixes freely, re-review for big ones.
- **Unblocks:** final editing rules and status flow.
- **Answer:**

### B2. Can a partner withdraw a deal, and can it come back?

- **Means:** a partner drops out of a deal. Do they lose their place permanently, and does DBGI need to confirm it?
- **Today:** there is no withdrawal. DBGI can only reject.
- **Choices:** (a) partner requests, DBGI confirms, the place in line is lost for good; (b) partner withdraws instantly, DBGI is notified; (c) withdrawn deals can be restored within a set time with their original place.
- **Unblocks:** the withdrawal feature (the next planned build).
- **Answer:**

### B3. What happens when two registrations turn out to be one deal, or one turns out to be two?

- **Means:** DBGI later learns two partner registrations are the same tender (merge), or one registration actually covers two separate lots (split). Who keeps first place, and what happens to approved prices?
- **Today:** DBGI groups matching registrations under one opportunity and lot when reviewing. There is no merge or split afterwards.
- **Choices:** (a) always keep each registration's original submission time for ranking, and re-review prices after any merge or split; (b) DBGI decides case by case with a written reason.
- **Unblocks:** merge and split tools.
- **Answer:**

### B4. Who decides Won, Lost, Cancelled, or On hold?

- **Means:** who marks the outcome of the government project, and should partners be able to report it?
- **Today:** only DBGI administrators set it, with a reason. Partners cannot.
- **Choices:** (a) keep DBGI only; (b) partners report, DBGI confirms.
- **Unblocks:** outcome tracking and win and loss reports.
- **Answer:**

### B5. What if two partners register at exactly the same moment?

- **Means:** first come, first served. Ties are very rare, but the rule should be known.
- **Today:** the earliest server-recorded submission time wins. Identical times share a rank and are marked as tied.
- **Choices:** (a) keep a shared rank, DBGI decides; (b) the better-documented registration wins.
- **Unblocks:** the final ranking rule.
- **Answer:**

### B6. How long does an early registration stay valid?

- **Means:** a partner registers a deal before the government posts the tender (an advance registration). How long can it wait, and how specific must it be to count?
- **Today:** no time limit and no reminders. DBGI judges whether the evidence is specific enough.
- **Choices:** (a) 60 days, with a reminder 7 days before, then DBGI reviews; (b) no limit, DBGI cleans up manually.
- **Unblocks:** expiry and reminder emails for early registrations.
- **Answer:**

### B7. What if the government postpones, cancels, or reposts a tender?

- **Means:** does the partner keep their place when the same project is posted again?
- **Today:** not handled. DBGI can only set the project status to Cancelled or On hold.
- **Choices:** (a) a repost of the same project keeps the original place in line; (b) a repost starts a new race; (c) DBGI decides each time.
- **Unblocks:** notice-change handling.
- **Answer:**

---

## Part C. Pricing (ask finance or the pricing owner)

### C1. How long is an approved special price valid?

- **Means:** when DBGI approves a discount for a deal, how many days before it expires, and when should the partner be reminded?
- **Today:** DBGI types an expiry date by hand each time (no default). Renewals add 30 days, which is already decided.
- **Choices:** (a) 90 days, reminder 14 days before; (b) until the tender's delivery date; (c) keep typing it each time.
- **Unblocks:** default expiry and reminders.
- **Answer:**

### C2. Are prices with or without VAT?

- **Means:** when a partner enters a requested price, or DBGI approves one, does it include 12% VAT?
- **Today:** the portal has no VAT handling. Each price is a single number.
- **Choices:** (a) all prices VAT-inclusive; (b) all VAT-exclusive; (c) set per product.
- **Unblocks:** price history and correct totals. This must be confirmed by finance before launch.
- **Answer:**

### C3. How should totals be rounded?

- **Means:** quantity times discounted price can produce fractions of a centavo.
- **Today:** line totals are rounded to two decimals.
- **Choices:** (a) round each line to 2 decimals, add the lines; (b) round only the grand total.
- **Unblocks:** totals that match DBGI's quotations.
- **Answer:**

### C4. Can DBGI approve a price for a product that is not in the catalog yet?

- **Means:** partners can request products not in the portal's list (typed by hand). Can those get an approved price?
- **Today:** partners can request them, but they get no price review at all. Price approvals are only created for catalog products, so a typed product cannot receive an approved price.
- **Choices:** (a) DBGI adds the product to the catalog first, then it gets reviewed; (b) approve it as typed, under an "Other products" group.
- **Unblocks:** the catalog onboarding rule.
- **Answer:**

### C5. What can partners see about prices?

- **Means:** list prices, their own approved prices, or nothing until approved?
- **Today:** partners see the list price at request time and their own approved prices. They never see other partners' prices.
- **Choices:** (a) keep today's rule; (b) hide list prices too.
- **Unblocks:** final price visibility in screens and exports.
- **Answer:**

---

## Part D. Later (needed before launch, not now)

### D1. Repeat orders on an approved price

- **Means:** after approval, a partner places more orders for the same customer. What proof is needed, and how does DBGI spot duplicates?
- **Today:** not built yet. It depends on Part C.
- **Ask:** What should DBGI check before honouring a repeat order at the special price (for example a purchase order, the same end-user, the same product)?
- **Answer:**

### D2. Who gets which emails?

- **Means:** which people receive the portal's email notifications, on the partner side and at DBGI.
- **Today:** every active user at the partner company receives each notification. DBGI staff get no emails and work from the dashboard queues.
- **Choices:** (a) keep today's rule; (b) email only the person who submitted; (c) also email DBGI reviewers when something needs action.
- **Answer:**

### D3. Records, backups, and recovery

- **Means:** how long to keep old deals and files, and how quickly the portal must be back after a failure.
- **Today:** the portal is not in production yet. Nothing is deleted automatically, and no backup schedule exists.
- **Choices:** (a) keep everything for 5 years, daily backups, back within one working day; (b) IT sets the targets.
- **Answer:**

### D4. Business hours and holidays

- **Means:** deadlines like "one working day" need a definition.
- **Today:** the portal uses Philippine time and counts calendar days (for example, a renewal adds 30 calendar days). There are no working-day or holiday rules.
- **Choices:** (a) Monday to Friday, Philippine public holidays excluded, 5:00 PM cutoff; (b) calendar days only.
- **Answer:**

---

## After the answers come in

Record each answer in the roadmap's decision register ([PRODUCT_ROADMAP_2026-10-21.md](PRODUCT_ROADMAP_2026-10-21.md), section 12)
with the date and who decided. Unanswered questions stay open. Work that does not depend on them continues meanwhile.
