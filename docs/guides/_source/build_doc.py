"""Build the 'Deal Registration, Made Simple' Word guide with wordcraft-cli (no Markdown conversion)."""

import json
import os
import re
import subprocess

WC = r"C:\Program Files\WordCraft\wordcraft-cli.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES = os.path.join(HERE, "slides")
OUT = os.path.join(HERE, "Deal Registration Guide.docx")

NAVY, TEAL, MUTED, LIGHT = "12384D", "1B7FA6", "5B6B7A", "E4EEF2"

cmds = []


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


after_table = False


def start(style):
    """Begin a block in `style`, dropping direct formatting carried over from the previous paragraph."""
    global after_table
    c("para.style", {"style": style})
    c("para.reset")
    c("format.resetChar")
    if after_table:
        c("para.set", {"props": {"spaceBefore": 10}})
        after_table = False


def para(text, style="Normal"):
    start(style)
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
    for i, item in enumerate(items):
        runs(item)
        c("text.newParagraph")
    if numbered:
        c("para.numbering", {"off": True})
    else:
        c("para.bullets", {"off": True})


def callout(text, color=LIGHT):
    start("Normal")
    c("para.shading", {"color": color})
    c("para.borders", {"kind": "left", "width": 3, "color": TEAL})
    runs(text)
    c("text.newParagraph")
    c("para.shading", {"color": None})
    c("para.borders", {"kind": "none"})


def picture(slide_no, caption, width=440):
    start("Normal")
    c("para.keepNext")
    c("para.alignCenter")
    c(
        "insert.picture",
        {"path": os.path.join(SLIDES, f"slide-{slide_no:02d}.png"), "width": width, "alt": caption},
    )
    c("text.newParagraph")
    start("Caption")
    c("para.alignCenter")
    c("text.insert", {"text": caption})
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
c("para.set", {"props": {"spaceBefore": 120, "spaceAfter": 4}})
c("format.set", {"props": {"bold": True, "size": 30, "color": NAVY}})
c("text.insert", {"text": "Deal Registration, Made Simple"})
c("format.resetChar")
c("text.newParagraph")
c("para.set", {"props": {"spaceBefore": 0, "spaceAfter": 24}})
c("format.set", {"props": {"size": 14, "color": TEAL}})
c("text.insert", {"text": "How it works in general, and where our portal fits in"})
c("format.resetChar")
c("text.newParagraph")
c("para.set", {"props": {"spaceBefore": 0, "spaceAfter": 6}})
c("format.set", {"props": {"color": MUTED}})
c("text.insert", {"text": "DBGI Project Registration Portal  |  Learning guide  |  2026-10-26"})
c("format.resetChar")
c("text.newParagraph")
c("para.set", {"props": {"spaceBefore": 24}})
callout(
    '**How to use this guide:** read it alongside the slide deck "Deal Registration, Made Simple". '
    "The deck shows each idea as a picture; this guide explains the same ideas in words. "
    "One example runs through both: Pasig City Hall needs 20 printers."
)

# ---------- 1 ----------
h1("1. Why deal registration exists", page_break=True)
para(
    "DBGI usually does not sell straight to the customer. It sells through **partner companies** "
    "(dealers or resellers) who deal with the actual buyers."
)
para(
    "Now imagine Pasig City Hall needs 20 printers, and three of our dealers hear about it. Without any rules:"
)
bullets(
    [
        "All three chase the same customer.",
        "Each one asks DBGI for a bigger discount so they can beat the others.",
        "They undercut each other, which pushes our own brand's price down.",
        "The dealer who did the real work (visited the client, learned what they need) may lose to someone who only showed up with a lower price.",
    ]
)
para("Over time, dealers stop looking for new customers, because someone else may take the reward.")
picture(2, "Figure 1. Without rules, three dealers fight over one buyer.")
callout(
    "**Deal registration fixes this.** The dealer who finds a real opportunity first registers it with DBGI. "
    "If DBGI approves it, that dealer gets priority on that specific deal, usually with a better price, for a limited time."
)

# ---------- 2 ----------
h1("2. The four players")
table(
    [
        ["Player", "What they do", "Name in our portal"],
        [
            "DBGI",
            "Owns the product and the pricing. Decides who gets protection and what price.",
            "DBGI administrators",
        ],
        [
            "Dealer / partner",
            "Finds the buyer and sells to them. Registers the deal.",
            "Company users",
        ],
        [
            "End-user",
            "The actual buyer, often a government office such as Pasig City Hall.",
            "End-user",
        ],
        [
            "Competitors",
            "Other brands the buyer is considering. Helps DBGI judge the price needed to win.",
            "Canon, Epson, HP, Lexmark",
        ],
    ],
    [110, 211, 130],
)

# ---------- 3 ----------
h1("3. The whole flow in 8 steps")
para("Almost every company that runs deal registration follows the same shape:")
bullets(
    [
        '**Find.** A dealer learns about a real buying need, for example "Pasig needs 20 printers by December."',
        "**Register.** The dealer submits the details: who the customer is, what they need, how many, when, which competitors are involved, and the price they are asking for. They attach proof, such as a procurement notice.",
        "**Check.** DBGI reviews it. Is it real? Is it specific enough? Did another dealer already register the same deal?",
        "**Decide.** DBGI approves or rejects. If several dealers registered the same deal, DBGI decides who ranks first.",
        "**Price.** For an approved deal, DBGI approves a special price so the dealer can compete. This is a separate decision.",
        "**Protect.** The approval lasts a limited time. If the deal is not closed in time, it expires unless renewed.",
        "**Close.** The dealer wins or loses the sale.",
        "**Verify the order.** When the dealer orders from DBGI, DBGI checks the order matches the approved deal before giving the special price.",
    ],
    numbered=True,
)
picture(5, "Figure 2. The eight steps. Teal steps are done by the dealer, navy steps by DBGI.")

# ---------- 4 ----------
h1("4. Who gets the deal?")
para("Steps 3 and 4 are where DBGI decides between dealers. Using the Pasig example:")
table(
    [
        ["Date", "Dealer", "What they registered", "Result"],
        [
            "Sep 28",
            "Dealer C",
            '"Pasig might buy printers soon." No contact, product, or quantity.',
            "Too vague: asked for details",
        ],
        [
            "Oct 1",
            "Dealer A",
            "Pasig City Hall, 20 printers, model listed, notice attached.",
            "Rank 1",
        ],
        ["Oct 3", "Dealer B", "Same deal, also specific, with proof.", "Rank 2"],
    ],
    [55, 70, 206, 120],
)
para(
    "Dealer C was earliest, but the claim was too vague to protect. The usual rule is: **the first claim that is real and specific wins.** "
    "Exactly how strict to be is a DBGI policy decision."
)
picture(6, "Figure 3. First valid and specific claim usually wins.")

# ---------- 5 ----------
h1("5. Two separate approvals")
para(
    '"This deal is yours" and "you get this price" are two different decisions. Our portal keeps them separate on purpose.'
)
h2("Registration approval: is this deal yours?")
bullets(
    [
        "Is it a real, specific opportunity?",
        "Is it a duplicate of another registration?",
        "Who registered first?",
    ]
)
para("The result is approved or rejected, plus a rank (first, second, and so on).")
h2("Price approval: what price can you get?")
para("For one printer in the Pasig deal:")
table(
    [
        ["Price", "Amount", "Who sets it"],
        ["List price", "PHP 10,000", "DBGI price list"],
        ["Dealer requested", "PHP 9,000", "The dealer asks"],
        ["DBGI approved", "PHP 9,200", "DBGI decides"],
    ],
    [150, 150, 151],
)
callout(
    "**Remember:** a requested price is never an approved price. The dealer asks; DBGI decides."
)
picture(7, "Figure 4. Registration approval and price approval are separate.")

# ---------- 6 ----------
h1("6. Protection does not last forever")
para(
    'Approvals expire, so nobody can "park" a deal and block others indefinitely. Our portal gives **30 days** per approval or renewal.'
)
bullets(
    [
        "**Renewed before expiry:** 30 more days are added to the old expiry date. Protection continues with no gap.",
        "**Renewed after expiry:** the new 30 days start from the renewal approval date. The days in between are not covered, so orders placed in that gap do not get the special price.",
    ]
)
picture(8, "Figure 5. Renewing before expiry avoids a gap.")

# ---------- 7 ----------
h1("7. Checking the order")
para(
    "Before DBGI honors the special price on an order, all five of these must match the approved deal:"
)
bullets(
    [
        "Same dealer company",
        "Same End-user",
        "Same product",
        "Order date inside the approval period",
        "Approval still active",
    ],
    numbered=True,
)
para(
    "If everything matches, the special price applies. If anything does not match, DBGI reviews it first. "
    "This stops a discount approved for Pasig from being used for a different customer."
)
picture(9, "Figure 6. Every order is checked against the approved deal.")

# ---------- 8 ----------
h1("8. Dealers never see each other's deals")
para(
    "DBGI sees everything: all dealers, all deals, all prices, and all rankings. Each dealer sees **only its own** registrations, prices, evidence, and rank."
)
para(
    "If dealers could see each other's customers and prices, the whole system would break. Our portal enforces this on the server, not just by hiding buttons on the screen."
)

# ---------- 9 ----------
h1("9. Words you will hear at work", page_break=True)
table(
    [
        ["Term", "Plain meaning"],
        ["Matching", "Checking whether two registrations are really the same deal"],
        ["Opportunity / scope", "The one real deal that several registrations point to"],
        ["Rank", "Who is first, second, and so on for that deal"],
        ["Commercial approval", "The price decision"],
        ["Renewal", "Extending an approval (+30 days in our portal)"],
        ["Reorder", "The buyer orders more later: can the approved price be reused?"],
        ["Withdrawal", "The dealer says: I am no longer pursuing this deal"],
        [
            "Merge / split",
            "DBGI fixes mistakes: two registrations that are one deal, or one that is really two",
        ],
        ["Evidence", "Proof the deal is real, such as a procurement notice"],
    ],
    [140, 311],
)

# ---------- 10 ----------
h1("10. The simple version, and where our portal is today", page_break=True)
para("Six steps are enough to keep deal registration fair and correct:")
table(
    [
        ["Step", "In our portal"],
        ["1. Dealer registers the deal with proof", "Done"],
        ["2. DBGI checks duplicates and who was first", "Done"],
        ["3. DBGI approves or rejects the registration", "Done"],
        ["4. DBGI approves a price separately, with an expiry", "Done"],
        ["5. DBGI checks each order before applying the price", "Not yet (roadmap Milestone 3)"],
        ["6. Dealers cannot see each other's deals", "Done"],
    ],
    [300, 151],
)
para("Also still missing: withdrawal requests, and merging or splitting deals.")

# ---------- 11 ----------
h1("11. Questions to ask your team")
para(
    "These are the decisions the portal is waiting on. Asking them is a good way to learn how DBGI wants things to work:"
)
bullets(
    [
        "How long does an approval last, and how do renewals work?",
        "When two dealers register the same deal, what decides who is first?",
        "Can a dealer edit a registration after submitting it?",
        "If a dealer withdraws, does the next dealer move up?",
        "How are discounts calculated: with or without VAT, and how is rounding done?",
    ],
    numbered=True,
)

# ---------- summary ----------
h2("Deal registration in one sentence")
callout(
    "The dealer who finds a real deal first registers it. DBGI confirms it, protects it for a limited time "
    "with a special price, and checks the order before honoring that price."
)
c("format.set", {"props": {"size": 9, "color": MUTED}})
c("text.insert", {"text": "Portal status reflects the project roadmap as of 2026-10-26."})
c("format.resetChar")

c("insert.pageNumber", {"position": "bottom", "align": "center"})

script = {"commands": cmds, "save": [OUT]}
path = os.path.join(HERE, "doc-script.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(script, f, ensure_ascii=False, indent=1)
r = subprocess.run([WC, "run", "--script", path], capture_output=True, text=True, encoding="utf-8")
print(r.stdout[-500:], r.stderr[-2000:])
if r.returncode == 0:
    info = subprocess.run([WC, "info", OUT], capture_output=True, text=True, encoding="utf-8")
    print(info.stdout[:400])
