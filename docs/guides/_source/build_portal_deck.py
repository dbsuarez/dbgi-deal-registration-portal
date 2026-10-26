"""Build the 'Using the DBGI Project Registration Portal' walkthrough deck with deckcraft-cli."""

import os
import sys

from deck_lib import (
    GREEN,
    INK,
    LIGHT,
    MUTED,
    NAVY,
    SAND,
    TEAL,
    WHITE,
    Slide,
    c,
    run,
)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pylib"))
from PIL import Image  # noqa: E402

OUT = os.path.join(HERE, "portal-guide.deckcraft")
PNG_DIR = os.path.join(HERE, "portal-slides")
CROPS = os.path.join(HERE, "crops")
os.makedirs(PNG_DIR, exist_ok=True)

BORDER = "#C9D6DE"
COMPANY, ADMIN = "Company user", "DBGI administrator"

slides = []


def slide(fn):
    slides.append(fn)
    return fn


def role_chip(s, role, step=None):
    col = TEAL if role == COMPANY else NAVY
    label = f"Step {step}  |  {role}" if step else role
    s.box([690, 40, 220, 28], label, fill=col, size=12, color=WHITE, bold=True)


def head(s, title, subtitle=None, role=None, step=None):
    s.box([60, 30, 56, 6], fill=TEAL, preset="rect")
    s.text([56, 42, 630 if role else 850, 50], title, size=26, bold=True, color=NAVY)
    if subtitle:
        s.text([58, 90, 850, 28], subtitle, size=14, color=MUTED)
    if role:
        role_chip(s, role, step)


def pic(s, name, box, align="center"):
    """Insert a crop scaled to fit `box` [x, y, w, h], keeping its aspect ratio."""
    path = os.path.join(CROPS, f"{name}.png")
    w, h = Image.open(path).size
    bx, by, bw, bh = box
    scale = min(bw / w, bh / h)
    pw, ph = round(w * scale, 1), round(h * scale, 1)
    x = bx + (bw - pw) / 2 if align == "center" else bx
    s.add("insert.picture", {"path": path, "rect": [x, by, pw, ph]})
    s.add("shape.line", {"color": BORDER, "width": 1})
    return [x, by, pw, ph]


def steps(s, rect, items, size=14, title=None):
    y = rect[1]
    if title:
        s.text([rect[0], y, rect[2], 26], title, size=15, bold=True, color=NAVY)
        y += 30
    s.box(
        [rect[0], y, rect[2], rect[3] - (y - rect[1])],
        "\n".join(items),
        preset="rect",
        size=size,
        color=INK,
        align="left",
        anchor="top",
    )
    s.add("format.numbering", {"on": True, "scheme": "arabicPeriod", "color": TEAL})
    s.add("format.paragraph", {"spaceAfter": 6})
    s.add("format.margins", {"left": 4, "right": 4, "top": 2})


def tip(s, rect, text, icon="lightbulb", fill=LIGHT, color=NAVY, size=13):
    s.note(rect, text, fill=fill, color=color, size=size, icon=icon)


WARN_FILL, WARN_INK = "#FDF1D6", "#8A5A00"


# 1 ---------------------------------------------------------------- title
@slide
def s_title(s):
    s.add("design.background", {"color": NAVY})
    s.box([60, 140, 70, 8], fill=SAND, preset="rect")
    s.text(
        [56, 160, 860, 110],
        "Using the DBGI Project Registration Portal",
        size=40,
        bold=True,
        color=WHITE,
    )
    s.text(
        [58, 272, 840, 40],
        "One deal, from registration to approved price, with real screens",
        size=21,
        color="#B9D4E0",
    )
    s.text(
        [58, 440, 840, 30],
        "Walkthrough for company users and DBGI administrators  |  2026-10-26",
        size=14,
        color="#8FB3C4",
    )


# 2 ---------------------------------------------------------------- two kinds of users
@slide
def s_users(s):
    head(
        s, "Two kinds of users", "Everyone signs in at the same portal, but sees different screens"
    )
    cards = [
        (
            COMPANY,
            "briefcase",
            TEAL,
            "Works for a partner dealer.\nRegisters deals, answers DBGI's questions, and checks decisions and approved prices.",
            "Uses: Registrations, Notifications, Rankings, Help",
        ),
        (
            ADMIN,
            "building",
            NAVY,
            "Works for DBGI.\nReviews every registration, decides matches and prices, and keeps master data clean.",
            "Uses: Registration pages and the Administration area",
        ),
    ]
    for i, (name, icon, col, desc, uses) in enumerate(cards):
        x = 60 + i * 435
        s.box([x, 135, 415, 300], fill=WHITE, line=BORDER, preset="rect")
        s.box([x, 135, 415, 8], fill=col, preset="rect")
        s.box([x + 24, 165, 56, 56], fill=col, preset="ellipse")
        s.icon(icon, [x + 38, 179, 28, 28], WHITE)
        s.text([x + 96, 172, 300, 40], name, size=22, bold=True, color=NAVY, anchor="middle")
        s.text([x + 24, 240, 370, 120], desc, size=15, color=INK)
        s.box([x + 24, 375, 367, 40], uses, fill=LIGHT, size=13, color=NAVY, bold=True)
    tip(
        s,
        [60, 455, 850, 46],
        "Every slide that follows shows a chip in the top-right corner saying who does that step.",
        icon="info",
    )


# 3 ---------------------------------------------------------------- journey map
@slide
def s_journey(s):
    head(
        s,
        "The journey we will follow",
        "A real registration, DBGI-000012, created in the portal's test environment",
    )
    s.box([60, 128, 300, 330], fill=LIGHT, preset="rect")
    s.text([76, 138, 270, 26], "The example deal", size=16, bold=True, color=NAVY)
    s.text(
        [76, 168, 272, 290],
        "Dealer: DEMO ONLY - Sample Partner (a demo company)\n\n"
        "Buyer (End-user): Pasig City Schools Division Office\n\n"
        "Needs: 20 laser printers, model M1820W\nList price: PHP 10,000 each\n\n"
        "Competitor: Canon at PHP 9,300\n\nDealer asks DBGI for: PHP 9,000",
        size=13,
        color=INK,
    )
    journey = [
        ("Sign in", "Both", MUTED),
        ("Create and submit the registration", COMPANY, TEAL),
        ("Review it and ask for a correction", ADMIN, NAVY),
        ("Correct it and resubmit", COMPANY, TEAL),
        ("Confirm the registration", ADMIN, NAVY),
        ("Approve the price", ADMIN, NAVY),
        ("See the decision and approved price", COMPANY, TEAL),
        ("Check the ranking", COMPANY, TEAL),
    ]
    for i, (what, who, col) in enumerate(journey):
        y = 128 + i * 42
        s.box(
            [385, y, 34, 34],
            str(i + 1),
            fill=col,
            preset="ellipse",
            size=14,
            color=WHITE,
            bold=True,
        )
        s.box([428, y, 310, 34], what, fill=WHITE, line=BORDER, size=13, color=INK, align="left")
        s.add("format.margins", {"left": 10})
        s.text([746, y, 170, 34], who, size=12, color=col, bold=True, anchor="middle")
    tip(
        s,
        [60, 472, 850, 40],
        "Steps 3 and 4 are optional in real life: they only happen when DBGI needs more information.",
        icon="info",
    )


# 4 ---------------------------------------------------------------- sign in + list
@slide
def s_signin(s):
    head(
        s,
        "Sign in and find your way",
        "The registrations list is your home page",
        role="Both",
        step=1,
    )
    pic(s, "login", [60, 130, 230, 220])
    pic(s, "list", [310, 130, 600, 210])
    steps(
        s,
        [60, 370, 850, 140],
        [
            "Sign in with the username and password DBGI gave you. Test environments also show one-click test accounts.",
            "The top menu has Rankings, Notifications, Help, and Log out. DBGI administrators also see Administration.",
            "Company users start a deal with NEW REGISTRATION. Each row in the table is one registration; click its reference to open it.",
        ],
        size=13,
    )


# 5 ---------------------------------------------------------------- three badges
@slide
def s_badges(s):
    head(
        s,
        "Read the three status badges separately",
        "Every registration shows three badges. They answer different questions.",
    )
    cols = [
        (
            "Registration status",
            "Is the deal accepted by DBGI?",
            TEAL,
            [
                "Submitted",
                "Under review",
                "Changes requested",
                "Resubmitted",
                "Registered",
                "Review required after edit",
                "Rejected",
            ],
        ),
        (
            "Project status",
            "Is the procurement itself going ahead?",
            NAVY,
            ["Not linked", "Upcoming", "Active", "Won", "Lost", "Cancelled", "On hold"],
        ),
        (
            "Pricing status",
            "Has DBGI decided the price?",
            GREEN,
            [
                "Pending",
                "Changes requested",
                "Partially approved",
                "Approved",
                "Rejected",
                "Expired",
            ],
        ),
    ]
    for i, (name, q, col, values) in enumerate(cols):
        x = 60 + i * 290
        s.box([x, 125, 270, 318], fill=WHITE, line=BORDER, preset="rect")
        s.box([x, 125, 270, 40], name, fill=col, size=16, color=WHITE, bold=True, preset="rect")
        s.text([x + 14, 170, 242, 40], q, size=13, color=MUTED)
        for j, v in enumerate(values):
            s.box([x + 14, 212 + j * 31, 242, 25], v, fill=LIGHT, size=12, color=NAVY, align="left")
            s.add("format.margins", {"left": 10})
    tip(
        s,
        [60, 455, 850, 50],
        "Example: a deal can be Registered with Pricing still Pending. Hover over any badge in the portal to see what it means.",
        icon="lightbulb",
    )


# 6 ---------------------------------------------------------------- create: opportunity
@slide
def s_create_opportunity(s):
    head(
        s,
        "Create a registration: who and what",
        "Start from Registrations, then NEW REGISTRATION",
        role=COMPANY,
        step=2,
    )
    pic(s, "enduser", [60, 128, 520, 300], align="left")
    steps(
        s,
        [600, 128, 310, 300],
        [
            "Type part of the buyer's name in End-user and pick the match. A green line confirms the address and that DBGI verified it.",
            "Not in the list? Use ADD MISSING END-USER. DBGI verifies it later.",
            "Enter the project title, bid date, and delivery date.",
            "Check the contact details. They are filled from your profile.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 446, 850, 56],
        "Register each real opportunity once. To fix something later, edit the existing registration instead of creating a new one.",
        icon="circle-alert",
        fill=WARN_FILL,
        color=WARN_INK,
    )


# 7 ---------------------------------------------------------------- create: competitor + product
@slide
def s_create_items(s):
    head(
        s,
        "Add the competitor and the products you need",
        "Both tables need at least one row",
        role=COMPANY,
        step=2,
    )
    pic(s, "competitor", [60, 125, 410, 250])
    pic(s, "product", [500, 125, 410, 250])
    steps(
        s,
        [60, 385, 410, 130],
        [
            "Select ADD COMPETITOR.",
            "Pick or type the brand and model, their bid price, and a remark. Only you and DBGI see this.",
        ],
        size=13,
    )
    steps(
        s,
        [500, 385, 410, 130],
        [
            "Select ADD PRODUCT and choose the catalog product.",
            "Enter quantity, the unit price you are requesting, and why you need it.",
        ],
        size=13,
    )


# 8 ---------------------------------------------------------------- create: evidence + submit
@slide
def s_create_evidence(s):
    head(
        s,
        "Describe your evidence and submit",
        "Evidence tells DBGI how you know this opportunity is real",
        role=COMPANY,
        step=2,
    )
    pic(s, "evidence-submit", [60, 125, 560, 260], align="left")
    steps(
        s,
        [640, 125, 270, 320],
        [
            "Explain how you learned about the deal, with dates and reference numbers if you have them.",
            "Add files if available. Never upload another company's pricing, IDs, or signatures.",
            "Tick the authorization box.",
            "Select CREATE REGISTRATION.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 400, 560, 100],
        "Requested prices are only proposals until DBGI approves them. Do not promise a requested price to the buyer.",
        icon="circle-alert",
        fill=WARN_FILL,
        color=WARN_INK,
    )


# 9 ---------------------------------------------------------------- after submit
@slide
def s_after_submit(s):
    head(
        s,
        "Right after you submit",
        "The registration gets a DBGI reference and waits for review",
        role=COMPANY,
        step=2,
    )
    pic(s, "submitted-top", [60, 125, 560, 120], align="left")
    pic(s, "submitted-pricing", [60, 262, 560, 240], align="left")
    steps(
        s,
        [640, 125, 270, 380],
        [
            "Note the reference, here DBGI-000012. Use it whenever you talk to DBGI.",
            "Badges show Submitted, Project: Not linked, and Pricing: Pending.",
            '"What happens next?" always tells you what to do now.',
            "The portal works out the discount you asked for (10%) and the total. Approved unit price stays Pending until DBGI decides.",
        ],
        size=13,
    )


# 10 --------------------------------------------------------------- notifications
@slide
def s_notifications(s):
    head(
        s,
        "Notifications keep you up to date",
        "Every submission and DBGI decision appears here",
        role=COMPANY,
    )
    pic(s, "notifications", [60, 125, 560, 330], align="left")
    steps(
        s,
        [640, 125, 270, 330],
        [
            "Open NOTIFICATIONS from the top menu.",
            "Unread items are marked. Select VIEW REGISTRATION to open the deal.",
            "Email may send a copy, but the portal notification is the official record.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 466, 850, 40],
        "Check Notifications daily, especially while a registration is waiting for you.",
        icon="bell",
    )


# 11 --------------------------------------------------------------- admin dashboard
@slide
def s_dashboard(s):
    head(
        s,
        "Start each day on the Operations dashboard",
        "Administration opens here; it lists what needs a DBGI decision",
        role=ADMIN,
        step=3,
    )
    pic(s, "dashboard", [60, 125, 560, 307], align="left")
    steps(
        s,
        [640, 125, 270, 330],
        [
            "The cards count work waiting: registration reviews, pricing decisions, End-users to verify, failed emails, and expiring approvals.",
            "The queues below list the actual items. Click a reference to open it.",
            "The left menu has every list, such as Registrations, Price approvals, and End-users.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 448, 850, 50],
        "The Danger Zone at the bottom permanently deletes data. Only superusers can open it.",
        icon="triangle-alert",
        fill=WARN_FILL,
        color=WARN_INK,
    )


# 12 --------------------------------------------------------------- start review
@slide
def s_start_review(s):
    head(
        s,
        "Open the registration and start the review",
        "Administrators see a DBGI review panel at the top",
        role=ADMIN,
        step=3,
    )
    pic(s, "start-review", [60, 125, 560, 278], align="left")
    steps(
        s,
        [640, 125, 270, 330],
        [
            "Read the system recommendation and match score. They are only suggestions.",
            "Compare the End-user, address, products, and evidence yourself.",
            "Write a short review reason and select START REVIEW. This only marks the review as started.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 420, 560, 80],
        "Never confirm a match from the score alone. Here the score is 53% against a different Pasig project.",
        icon="circle-alert",
        fill=WARN_FILL,
        color=WARN_INK,
    )


# 13 --------------------------------------------------------------- decision options
@slide
def s_decide(s):
    head(
        s,
        "Choose exactly one decision",
        "In the example, DBGI asks the dealer for the RFQ reference",
        role=ADMIN,
        step=3,
    )
    pic(s, "decision-options", [60, 125, 520, 335], align="left")
    rows = [
        (
            "Link to an existing opportunity",
            "This deal is the same procurement as one already in the portal.",
        ),
        ("Create a new whole opportunity", "No existing opportunity fits."),
        ("Request changes", "Something is missing or wrong. Write exact instructions."),
        ("Reject registration", "Give a clear business reason."),
    ]
    for i, (a, b) in enumerate(rows):
        y = 125 + i * 84
        s.text([600, y, 310, 24], a, size=14, bold=True, color=NAVY)
        s.text([600, y + 26, 310, 52], b, size=13, color=INK)
    tip(
        s,
        [60, 470, 850, 38],
        "The company is notified automatically after every decision.",
        icon="bell",
    )


# 14 --------------------------------------------------------------- company reads request
@slide
def s_read_request(s):
    head(
        s,
        "Read what DBGI needs",
        "The registration now shows Changes requested",
        role=COMPANY,
        step=4,
    )
    pic(s, "changes-requested", [60, 125, 600, 122], align="left")
    pic(s, "activity-reason", [60, 265, 600, 122], align="left")
    steps(
        s,
        [680, 125, 230, 300],
        [
            "Open the Changes requested notification, or the registration itself.",
            "Scroll to Activity. DBGI's exact instructions are under Request changes.",
            "Select EDIT REGISTRATION.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 405, 600, 90],
        "View changes under each Activity entry shows the before and after values for that step.",
        icon="info",
    )


# 15 --------------------------------------------------------------- fix and resubmit
@slide
def s_resubmit(s):
    head(
        s,
        "Fix only what was asked, then save",
        "The same registration goes back to DBGI",
        role=COMPANY,
        step=4,
    )
    pic(s, "edit-evidence", [60, 125, 450, 172], align="left")
    pic(s, "resubmitted", [60, 312, 600, 122], align="left")
    steps(
        s,
        [680, 125, 230, 330],
        [
            "Change only the fields DBGI mentioned. Here, the RFQ reference was added to the evidence.",
            "Review everything, then select SAVE CHANGES.",
            "The status becomes Resubmitted. DBGI reviews the corrected version.",
        ],
        size=13,
    )
    tip(
        s,
        [60, 448, 850, 50],
        "Editing a registration that was already Registered also sends it back for review.",
        icon="circle-alert",
        fill=WARN_FILL,
        color=WARN_INK,
    )


# 16 --------------------------------------------------------------- admin confirms
@slide
def s_confirm(s):
    head(
        s,
        "Check the changes, then confirm",
        "Activity shows exactly what the company changed",
        role=ADMIN,
        step=5,
    )
    pic(s, "activity-changes", [60, 125, 420, 200], align="left")
    pic(s, "create-opportunity", [500, 125, 410, 264], align="left")
    steps(
        s,
        [60, 340, 420, 170],
        [
            "Open the Company edit entry and compare old and new values.",
            "Start review again with a reason.",
            "Pick the final decision. Here: Create a new whole opportunity, because this is a school division purchase.",
        ],
        size=13,
    )
    tip(
        s,
        [500, 400, 410, 100],
        "Result: Registered, Project: Upcoming. The opportunity now exists and ranking can be calculated.",
        icon="circle-check",
        fill="#E3F4EC",
        color="#1D6B48",
    )


# 17 --------------------------------------------------------------- pricing
@slide
def s_pricing(s):
    head(
        s,
        "Approve the price",
        "Administration, Price approvals (or the dashboard's Pricing queue)",
        role=ADMIN,
        step=6,
    )
    pic(s, "pricing-top", [60, 125, 420, 232], align="left")
    pic(s, "pricing-items", [60, 372, 420, 130], align="left")
    steps(
        s,
        [500, 125, 410, 280],
        [
            "Open the pending category for the registration.",
            "Set Status: Approved, Partially approved, Rejected, or Changes requested.",
            "Write the rationale and set Valid until.",
            "Under Registration item approvals, add the item and its approved unit price.",
            "Select Save. Reviewed by and Reviewed at are filled in with your name and the time.",
        ],
        size=13,
    )
    tip(
        s,
        [500, 410, 410, 92],
        "Only this registration's items are offered, each labelled with its reference, such as DBGI-000012.",
        icon="info",
    )


# 18 --------------------------------------------------------------- company sees result
@slide
def s_result(s):
    head(
        s,
        "See the decision and the approved price",
        "All three badges now have an answer",
        role=COMPANY,
        step=7,
    )
    pic(s, "approved-top", [60, 125, 560, 119], align="left")
    pic(s, "approved-pricing", [60, 258, 560, 245], align="left")
    steps(
        s,
        [640, 125, 270, 380],
        [
            "Badges: Registered, Project: Upcoming, Pricing: Approved.",
            "Commercial approvals shows the decision, valid-until date, reviewer, and reason.",
            "Requested products shows the approved unit price: PHP 9,200, not the PHP 9,000 requested.",
            "Quote only the approved price, and only until the valid-until date.",
        ],
        size=13,
    )


# 19 --------------------------------------------------------------- rankings
@slide
def s_rankings(s):
    head(s, "Check your ranking", "RANKINGS in the top menu", role=COMPANY, step=8)
    pic(s, "rankings", [60, 125, 850, 260])
    steps(
        s,
        [60, 395, 850, 110],
        [
            "Each row is a confirmed opportunity your company registered for, with your rank and the date you became eligible.",
            "You only see your own rank. Other companies and their registrations stay private.",
        ],
        size=13,
    )


# 20 --------------------------------------------------------------- other scenarios
@slide
def s_other(s):
    head(s, "Other situations you will meet", "Covered step by step in the portal's Help page")
    rows = [
        (
            "users",
            "Buyer missing from the End-user list",
            "Company: use Add missing End-user. Admin: Administration, End-users; check the official name and address, add aliases, then verify.",
        ),
        (
            "x",
            "Registration rejected",
            "Read the reason in Activity. Do not resubmit the same deal as a new registration.",
        ),
        (
            "mail",
            "An email failed to send",
            "Admin: Administration, Notification deliveries. Fix the address or settings, then retry. The portal notification was never lost.",
        ),
        (
            "calendar",
            "An approval is about to expire",
            "Admin: the dashboard's Expiring in 30 days card and Price renewals. Each renewal adds 30 days.",
        ),
    ]
    for i, (icon, a, b) in enumerate(rows):
        y = 128 + i * 92
        s.box([60, y, 54, 54], fill=TEAL, preset="ellipse")
        s.icon(icon, [74, y + 14, 26, 26], WHITE)
        s.text([130, y, 780, 26], a, size=15, bold=True, color=NAVY)
        s.text([130, y + 26, 780, 56], b, size=13, color=INK)


# 21 --------------------------------------------------------------- golden rules
@slide
def s_rules(s):
    head(s, "Golden rules", "If you remember nothing else, remember these")
    rules = [
        ("circle-alert", "A requested price is never an approved price."),
        ("file-text", "One registration per real opportunity. Edit it; do not duplicate it."),
        ("bell", "The portal notification is the official record. Email is only a copy."),
        (
            "message-circle",
            "Write reasons and instructions someone else can act on without asking you.",
        ),
        ("check", "Read the three badges separately: registration, project, pricing."),
        ("info", "Stuck? Open HELP. It has step-by-step guides for your role."),
    ]
    for i, (icon, t) in enumerate(rules):
        col, row = divmod(i, 3)
        x, y = 60 + col * 435, 130 + row * 120
        s.box([x, y, 415, 100], fill=LIGHT, preset="roundRect")
        s.box([x + 16, y + 26, 48, 48], fill=TEAL, preset="ellipse")
        s.icon(icon, [x + 28, y + 38, 24, 24], WHITE)
        s.text([x + 78, y + 10, 325, 80], t, size=15, color=NAVY, bold=True, anchor="middle")


# 22 --------------------------------------------------------------- quick reference
@slide
def s_reference(s):
    head(s, "Quick reference: where do I go?")
    rows = [
        ("I want to...", "Go to"),
        ("Register a new deal", "Registrations, then NEW REGISTRATION"),
        ("See what DBGI decided", "NOTIFICATIONS, then VIEW REGISTRATION"),
        (
            "Fix a registration DBGI sent back",
            "Open the registration, read Activity, EDIT REGISTRATION",
        ),
        (
            "See my approved price",
            "Open the registration: Commercial approvals and Requested products",
        ),
        ("See my rank", "RANKINGS"),
        ("Review a registration (DBGI)", "Administration dashboard, Registration review queue"),
        ("Decide a price (DBGI)", "Administration, Price approvals"),
        ("Get step-by-step help", "HELP in the top menu"),
    ]
    s.add("insert.table", {"rows": len(rows), "cols": 2, "rect": [60, 110, 850, 360]})
    s.add("table.style", {"style": "medium2-accent1"})
    for r, (a, b) in enumerate(rows):
        s.add("text.set", {"text": a, "cell": [r, 0]})
        s.add("text.set", {"text": b, "cell": [r, 1]})
    s.add("text.exit")
    s.add("format.size", {"size": 14})
    s.add("table.cellAlign", {"anchor": "middle"})
    s.add("table.columnWidth", {"col": 0, "width": 330})
    s.add("table.columnWidth", {"col": 1, "width": 520})


def build():
    for i, fn in enumerate(slides):
        s = Slide()
        if i == 0:
            s.add("design.theme", {"name": "Harbor"})
            s.add("slide.layout", {"layout": "blank"})
            src = None
        else:
            s.add("slide.last")
            s.add("slide.new", {"layout": "blank"})
            src = OUT
        fn(s)
        try:
            run(s.cmds, src=src, save=OUT)
        except SystemExit as exc:
            raise SystemExit(f"slide {i + 1} ({fn.__name__}): {exc}")
    run(
        [c("design.headerFooter", {"slideNumber": True, "hideOnTitle": True, "all": True})],
        src=OUT,
        save=OUT,
    )
    for i in range(len(slides)):
        run(
            [c("slide.go", {"index": i})],
            src=OUT,
            export=os.path.join(PNG_DIR, f"slide-{i + 1:02d}.png"),
            export_params={"slide": i},
        )
    print(f"built {len(slides)} slides -> {OUT}")


if __name__ == "__main__":
    build()
