"""Build the 'Using the DBGI Project Registration Portal' Word guide with wordcraft-cli commands."""

import json
import os
import re
import subprocess

WC = r"C:\Program Files\WordCraft\wordcraft-cli.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
CROPS = os.path.join(HERE, "crops")
OUT = os.path.join(HERE, "Portal User Guide.docx")

NAVY, TEAL, MUTED, LIGHT = "12384D", "1B7FA6", "5B6B7A", "E4EEF2"
WARN = "FDF1D6"
GOOD = "E3F4EC"

cmds = []
after_table = False
figure_no = 0


def c(command, params=None):
    cmds.append(
        {"command": command, "params": params} if params is not None else {"command": command}
    )


def runs(text):
    """Type text, turning **x** into bold runs."""
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        if i % 2:
            c("format.set", {"props": {"bold": True}})
            c("text.insert", {"text": part})
            c("format.resetChar")
        else:
            c("text.insert", {"text": part})


def start(style):
    """Begin a block in `style`, dropping direct formatting carried over from the previous paragraph."""
    global after_table
    c("para.style", {"style": style})
    c("para.reset")
    c("format.resetChar")
    if after_table:
        c("para.set", {"props": {"spaceBefore": 10}})
        after_table = False


def para(text):
    start("Normal")
    runs(text)
    c("text.newParagraph")


def h1(text, page_break=False):
    if page_break:
        c("text.pageBreak")
    start("Heading1")
    c("para.keepNext")
    c("text.insert", {"text": text})
    c("text.newParagraph")


def h2(text):
    start("Heading2")
    c("para.keepNext")
    c("text.insert", {"text": text})
    c("text.newParagraph")


def bullets(items, numbered=False):
    start("Normal")
    if numbered:
        c("para.numbering", {"kind": "numbered"})
        c("para.restartNumbering")
    else:
        c("para.bullets")
    for item in items:
        runs(item)
        c("text.newParagraph")
    c("para.numbering" if numbered else "para.bullets", {"off": True})


def callout(text, color=LIGHT, edge=TEAL):
    start("Normal")
    c("para.shading", {"color": color})
    c("para.borders", {"kind": "left", "width": 3, "color": edge})
    runs(text)
    c("text.newParagraph")
    c("para.shading", {"color": None})
    c("para.borders", {"kind": "none"})


def warn(text):
    callout(text, color=WARN, edge="E3B21C")


def good(text):
    callout(text, color=GOOD, edge="2EA36F")


def picture(name, caption, width=451):
    global figure_no
    figure_no += 1
    start("Normal")
    c("para.keepNext")
    c("para.alignCenter")
    c(
        "insert.picture",
        {"path": os.path.join(CROPS, f"{name}.png"), "width": width, "alt": caption},
    )
    c("text.newParagraph")
    start("Caption")
    c("para.alignCenter")
    c("text.insert", {"text": f"Figure {figure_no}. {caption}"})
    c("text.newParagraph")
    start("Normal")


def table(rows, widths):
    """A full-width table; `widths` are column widths in points summing to the 451 pt A4 text width."""
    global after_table
    start("Normal")
    c("insert.table", {"rows": len(rows), "cols": len(rows[0]), "style": "GridTable4AccentBlue"})
    c("table.autofit", {"mode": "fixed"})
    first = True
    for r, row in enumerate(rows):
        for col, cell in enumerate(row):
            if not first:
                c("text.tab")
            first = False
            if r == 0:
                # columnWidth acts on the caret's column, so size each column from its header cell
                c("table.columnWidth", {"width": widths[col]})
            runs(cell)
    c("caret.docEnd")
    after_table = True


def scenario(title, who, before, page_break=False):
    h1(title, page_break=page_break)
    para(f"**Who:** {who}")
    para(f"**Before you start:** {before}")


# ---------- document setup ----------
c("layout.size", {"name": "A4"})
c("layout.margins", {"preset": "normal"})
c(
    "styles.modify",
    {"style": "Normal", "chr": {"font": "Calibri", "size": 11}, "para": {"spaceAfter": 6}},
)
c(
    "styles.modify",
    {
        "style": "Heading1",
        "chr": {"font": "Calibri", "size": 18, "bold": True, "color": NAVY},
        "para": {"spaceBefore": 18, "spaceAfter": 8},
    },
)
c(
    "styles.modify",
    {
        "style": "Heading2",
        "chr": {"font": "Calibri", "size": 14, "bold": True, "color": TEAL},
        "para": {"spaceBefore": 12, "spaceAfter": 4},
    },
)

# ---------- title block ----------
c("para.style", {"style": "Normal"})
c("para.set", {"props": {"spaceBefore": 110, "spaceAfter": 4}})
c("format.set", {"props": {"bold": True, "size": 28, "color": NAVY}})
c("text.insert", {"text": "Using the DBGI Project Registration Portal"})
c("format.resetChar")
c("text.newParagraph")
start("Normal")
c("para.set", {"props": {"spaceAfter": 24}})
c("format.set", {"props": {"size": 14, "color": TEAL}})
c("text.insert", {"text": "Step-by-step scenarios for company users and DBGI administrators"})
c("format.resetChar")
c("text.newParagraph")
start("Normal")
c("format.set", {"props": {"color": MUTED}})
c("text.insert", {"text": "DBGI Project Registration Portal  |  User guide  |  2026-10-26"})
c("format.resetChar")
c("text.newParagraph")
start("Normal")
c("para.set", {"props": {"spaceBefore": 24}})
callout(
    "**How to use this guide:** every scenario follows one real registration, **DBGI-000012**, from the day it was "
    "submitted to the day its price was approved. The screenshots come from the portal's test environment, using a "
    "demo company called **DEMO ONLY - Sample Partner**. Your screens will show your own company and data."
)
callout(
    "**The example deal:** Pasig City Schools Division Office needs 20 monochrome laser printers (model M1820W, list "
    "price PHP 10,000 each). Canon is offering PHP 9,300, so the dealer asks DBGI for PHP 9,000."
)

# ---------- 1 ----------
h1("1. Before you start", page_break=True)
h2("Two kinds of users")
table(
    [
        ["Role", "Who they are", "What they do in the portal"],
        [
            "Company user",
            "Staff of a partner dealer",
            "Register deals, answer DBGI's questions, check decisions, approved prices, and rankings.",
        ],
        [
            "DBGI administrator",
            "DBGI staff",
            "Review registrations, decide matches and prices, maintain End-users, products, and other master data.",
        ],
    ],
    [100, 120, 231],
)
h2("Signing in and finding your way")
bullets(
    [
        "Sign in with the username and password DBGI gave you.",
        "The top menu has **Rankings**, **Notifications**, **Help**, and **Log out**. Administrators also see **Administration**.",
        "The **Registrations** page lists your registrations. Click a reference such as DBGI-000012 to open one.",
    ],
    numbered=True,
)
picture("list", "The Registrations page, with NEW REGISTRATION at the top right.")

h2("Reading the three status badges")
para(
    "Every registration shows three badges at the top. They answer different questions, so read them separately."
)
table(
    [
        ["Badge", "Question it answers", "Possible values"],
        [
            "Registration status",
            "Has DBGI accepted the deal?",
            "Submitted, Under review, Changes requested, Resubmitted, Registered, Review required after edit, Rejected",
        ],
        [
            "Project status",
            "Is the procurement itself going ahead?",
            "Not linked, Upcoming, Active, Won, Lost, Cancelled, On hold",
        ],
        [
            "Pricing status",
            "Has DBGI decided the price?",
            "Pending, Changes requested, Partially approved, Approved, Rejected, Expired",
        ],
    ],
    [110, 140, 201],
)
para(
    "A deal can be **Registered** while its pricing is still **Pending**. Hover over any badge in the portal to see what it means."
)

# ---------- 2 ----------
scenario(
    "2. Submit a new registration",
    "Company user",
    "the buyer's name, the project title, bid and delivery dates, at least one competitor offer, the product and "
    "quantity you need, the price you want to request, and a description of your evidence.",
)
h2("Step 1: who and what")
bullets(
    [
        "On the Registrations page, select **NEW REGISTRATION**.",
        "In **End-user**, type part of the buyer's name and pick the match. A green line confirms the address and that DBGI verified it.",
        "If the buyer is not listed, select **ADD MISSING END-USER**. DBGI verifies new End-users later.",
        "Enter the project title, bid date, and delivery date.",
        "Check the contact details. They are filled in from your profile.",
    ],
    numbered=True,
)
picture("enduser", "Searching for the End-user.")
warn(
    "Register each real opportunity **once**. To fix something later, edit the existing registration. Do not create a second one."
)
h2("Step 2: competitor and products")
bullets(
    [
        "Under Competitor items, select **ADD COMPETITOR**. Pick or type the brand and model, enter their bid price, and add a remark. Only your company and DBGI can see this.",
        "Under Requested products, select **ADD PRODUCT**. Choose the catalog product, then enter quantity, the unit price you are requesting, and your justification.",
    ],
    numbered=True,
)
picture("competitor", "Adding a competitor offer.", width=300)
picture("product", "Adding a requested product.", width=320)
h2("Step 3: evidence and submit")
bullets(
    [
        "In **Evidence description**, explain how you learned about the deal. Include dates and reference numbers if you have them.",
        "Add files if available. Never upload another company's pricing, personal IDs, or signatures.",
        "Tick **I confirm that I am authorized to share this evidence with DBGI for review**.",
        "Select **CREATE REGISTRATION**.",
    ],
    numbered=True,
)
picture("evidence-submit", "The Evidence section and the CREATE REGISTRATION button.")
h2("Expected result")
good(
    "The registration gets a DBGI reference (here **DBGI-000012**) and shows **Submitted**, **Project: Not linked**, and "
    "**Pricing: Pending**. A Submission confirmed notification appears, and the Activity list records the submission."
)
picture("submitted-top", "The new registration with its reference and badges.")
picture(
    "submitted-pricing",
    "The portal works out the requested discount and total. The approved price stays Pending.",
)
warn("A requested price is only a proposal. Do not promise it to the buyer until DBGI approves it.")

# ---------- 3 ----------
scenario(
    "3. Follow your registration through Notifications", "Company user", "a submitted registration."
)
bullets(
    [
        "Select **NOTIFICATIONS** in the top menu.",
        "Unread notifications are marked. Select **VIEW REGISTRATION** to open the deal.",
        "Email may send you a copy, but the portal notification is the official record.",
    ],
    numbered=True,
)
picture("notifications", "The Notifications page.")

# ---------- 4 ----------
scenario(
    "4. Review a registration and request changes",
    "DBGI administrator",
    "a registration with status Submitted. In the example, the evidence did not say which procurement it belonged "
    "to, so DBGI asked for the RFQ reference.",
)
h2("Step 1: find the work")
bullets(
    [
        "Sign in. Administrators land on the **Operations dashboard**.",
        "The cards count what is waiting: registration reviews, pricing decisions, End-users to verify, failed emails, and approvals expiring within 30 days.",
        "Open the registration from the **Registration review queue**, or open it from the Registrations page.",
    ],
    numbered=True,
)
picture("dashboard", "The Operations dashboard.")
warn(
    "The **Danger Zone** at the bottom of the dashboard permanently deletes data. Only superusers can open it."
)
h2("Step 2: start the review")
bullets(
    [
        "Read the **System recommendation** and **Match score**. They are suggestions, not decisions.",
        "Compare the End-user, address, products, and evidence yourself.",
        "Write a short **Review reason** and select **START REVIEW**. This only records that the review has started.",
    ],
    numbered=True,
)
picture("start-review", "The DBGI review panel before the review starts.")
warn(
    "Never confirm a match from the score alone. In the example the score was 53% against a different Pasig project."
)
h2("Step 3: choose exactly one decision")
table(
    [
        ["Decision", "Use it when"],
        [
            "Link to an existing opportunity",
            "The registration belongs to a procurement that is already in the portal.",
        ],
        ["Create a new whole opportunity", "No existing opportunity fits."],
        [
            "Request changes",
            "Information is missing or wrong. Write exact instructions the company can follow.",
        ],
        [
            "Reject registration",
            "The registration should not proceed. Give a clear business reason.",
        ],
    ],
    [170, 281],
)
picture("decision-options", "Requesting changes with exact instructions.")
h2("Expected result")
good(
    "The registration shows **Changes requested**. The company receives a notification and can read the instructions in Activity."
)

# ---------- 5 ----------
scenario(
    "5. Correct a registration and resubmit",
    "Company user",
    "a registration with status Changes requested.",
)
bullets(
    [
        "Open the **Changes requested** notification, or open the registration.",
        "Scroll to **Activity**. DBGI's exact instructions are under the **Request changes** entry.",
        "Select **EDIT REGISTRATION**.",
        "Change only the fields DBGI mentioned. In the example, the RFQ reference was added to the evidence description.",
        "Review the whole record and select **SAVE CHANGES**.",
    ],
    numbered=True,
)
picture("changes-requested", "The registration after DBGI requested changes.")
picture("activity-reason", "DBGI's instructions in Activity.")
picture("edit-evidence", "Adding the requested RFQ reference to the evidence.", width=380)
h2("Expected result")
good(
    "The status becomes **Resubmitted** and the registration goes back to DBGI. Activity records exactly what changed."
)
picture("resubmitted", "The corrected registration, back with DBGI.")
warn("Editing a registration that is already **Registered** also sends it back for review.")

# ---------- 6 ----------
scenario(
    "6. Check the correction and confirm the registration",
    "DBGI administrator",
    "a Resubmitted registration.",
)
bullets(
    [
        "Open the registration. In **Activity**, open **View changes** under **Company edit** to compare old and new values.",
        "Write a review reason and select **START REVIEW** again.",
        "Choose the final decision. In the example: **Create a new whole opportunity**, because the RFQ shows a school division purchase separate from the City Mayor's Office project.",
        "Write the **Decision reason** and select **CREATE AND LINK NEW OPPORTUNITY** (or **LINK EXISTING OPPORTUNITY**).",
    ],
    numbered=True,
)
picture("activity-changes", "Activity shows the old and new evidence text.")
picture("create-opportunity", "Creating a new whole opportunity.")
h2("Expected result")
good(
    "The registration shows **Registered** and **Project: Upcoming**. The opportunity now exists, rankings can be "
    "calculated, and the company receives a Registration confirmed notification."
)

# ---------- 7 ----------
scenario(
    "7. Approve the price",
    "DBGI administrator",
    "a Registered registration with a Pending pricing category.",
)
bullets(
    [
        "Open **Administration**, then **Price approvals**, or select the registration in the dashboard's **Pricing queue**.",
        "Set **Status** to Approved, Partially approved, Rejected, or Changes requested.",
        "Write the **Rationale**, select yourself in **Reviewed by**, and fill in **Reviewed at** and **Valid until**.",
        "Under **Registration item approvals**, select **Add another Registration item approval**, choose the item, and enter the **Approved unit price**.",
        "Select **Save**.",
    ],
    numbered=True,
)
picture("pricing-top", "The pricing decision form.")
picture("pricing-items", "Entering the approved unit price for the item.")
warn(
    "The item list can show the same product several times, one for each registration that requested it. Make sure you "
    "choose the item that belongs to this registration."
)
h2("Expected result")
good(
    "The pricing list shows **Approved** with its valid-until date, and the company receives a **Price request approved** notification."
)

# ---------- 8 ----------
scenario(
    "8. See the decision and the approved price",
    "Company user",
    "a registration for which DBGI has made a pricing decision.",
)
bullets(
    [
        "Open the **Price request approved** notification and select **VIEW REGISTRATION**.",
        "Check the badges: **Registered**, **Project: Upcoming**, **Pricing: Approved**.",
        "Under **Commercial approvals**, read the decision, the valid-until date, the reviewer, and the reason.",
        "Under **Requested products**, read the **Approved unit price**. In the example it is PHP 9,200, not the PHP 9,000 requested.",
    ],
    numbered=True,
)
picture("approved-top", "All three badges now have an answer.")
picture("approved-pricing", "The approved price and its validity.")
warn(
    "Quote only the **approved** unit price, and only until the valid-until date. Never use a requested price for an item that has no approval."
)
picture(
    "notifications-after", "The notifications for DBGI-000012 from submission to price approval."
)

# ---------- 9 ----------
scenario("9. Check your ranking", "Company user", "at least one Registered registration.")
bullets(
    [
        "Select **RANKINGS** in the top menu.",
        "Each row is a confirmed opportunity your company registered for, with your rank and the date you became eligible.",
        "You only see your own rank. Other companies and their registrations stay private.",
    ],
    numbered=True,
)
picture("rankings", "The Opportunity rankings page.")

# ---------- 10 ----------
h1("10. Other situations")
para("These are described step by step on the portal's **Help** page.")
h2("The buyer is missing from the End-user list")
bullets(
    [
        "**Company user:** select **ADD MISSING END-USER** on the registration form and complete the fields. The help buttons on each field show examples.",
        "**DBGI administrator:** open **Administration**, then **End-users**, and select the pending organization.",
        "Compare the name and address with an official source, correct them, and add aliases instead of creating a duplicate.",
        "Verify the End-user, then return to the linked registration and select **REFRESH SUGGESTION**.",
    ],
    numbered=True,
)
h2("A registration was rejected")
bullets(
    [
        "Open the registration and read DBGI's reason in **Activity**.",
        "Rejection is a decision about the registration, not a statement that the buyer cancelled the project.",
        "Do not resubmit the same deal as a new registration. Contact DBGI if you believe the decision is wrong.",
    ],
    numbered=True,
)
h2("An email failed to send (DBGI administrator)")
bullets(
    [
        "Open **Administration**, then **Notification deliveries**, and select the failed delivery.",
        "Read the error. Confirm the recipient's email address is correct.",
        "Fix the address or mail settings, then select the record and run **Retry selected failed email deliveries**.",
        "Refresh and confirm the status is **Sent**. The portal notification was available the whole time.",
    ],
    numbered=True,
)
h2("An approval is about to expire")
bullets(
    [
        "The dashboard's **Expiring in 30 days** card lists approvals that will expire soon.",
        "Renewals are handled under **Administration**, **Price renewals**. Each approved renewal adds 30 days.",
    ],
    numbered=True,
)

# ---------- 11 ----------
h1("11. Golden rules")
bullets(
    [
        "A requested price is never an approved price.",
        "One registration per real opportunity. Edit it; do not duplicate it.",
        "The portal notification is the official record. Email is only a copy.",
        "Write reasons and instructions that someone else can act on without asking you.",
        "Read the three badges separately: registration, project, and pricing.",
        "Stuck? Open **HELP**. It shows step-by-step guides for your role.",
    ]
)

# ---------- 12 ----------
h1("12. Quick reference")
table(
    [
        ["I want to...", "Go to"],
        ["Register a new deal", "Registrations, then NEW REGISTRATION"],
        ["See what DBGI decided", "NOTIFICATIONS, then VIEW REGISTRATION"],
        [
            "Fix a registration DBGI sent back",
            "Open the registration, read Activity, then EDIT REGISTRATION",
        ],
        [
            "See my approved price",
            "Open the registration: Commercial approvals and Requested products",
        ],
        ["See my rank", "RANKINGS"],
        ["Review a registration (DBGI)", "Administration dashboard, Registration review queue"],
        ["Decide a price (DBGI)", "Administration, Price approvals"],
        ["Verify a new End-user (DBGI)", "Administration, End-users"],
        ["Retry a failed email (DBGI)", "Administration, Notification deliveries"],
        ["Get step-by-step help", "HELP in the top menu"],
    ],
    [180, 271],
)

# ---------- 13 ----------
h1("13. Things to watch for in the current version")
bullets(
    [
        "The date fields on the registration form display dates as month/day/year while you type. After saving, the portal shows them as year-month-day (for example 2026-12-01).",
        "Pricing decisions are made in the Administration area, not on the registration page. **Reviewed by** must be selected by hand.",
        "The item list in a pricing decision can repeat the same product from several registrations. Check that you picked the right one.",
        "An administrator's registration page can show the green **Automatically matched** message even when an administrator confirmed the match by hand. Check Activity to see who decided.",
    ]
)
start("Normal")
c("format.set", {"props": {"size": 9, "color": MUTED}})
c("text.insert", {"text": "Screens captured from the portal's test environment on 2026-10-26."})
c("format.resetChar")

c("insert.pageNumber", {"position": "bottom", "align": "center"})

script = {"commands": cmds, "save": [OUT]}
path = os.path.join(HERE, "portal-doc-script.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(script, f, ensure_ascii=False, indent=1)
r = subprocess.run([WC, "run", "--script", path], capture_output=True, text=True, encoding="utf-8")
print(r.stdout[-300:], r.stderr[-2000:])
if r.returncode == 0:
    info = json.loads(
        subprocess.run([WC, "info", OUT], capture_output=True, text=True, encoding="utf-8").stdout
    )
    print("pages:", info["pages"])
