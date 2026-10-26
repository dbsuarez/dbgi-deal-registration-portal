"""Build the 'Deal Registration, Made Simple' teaching deck with deckcraft-cli."""

import os

from deck_lib import (
    CORAL,
    GREEN,
    INK,
    LIGHT,
    MINT,
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
OUT = os.path.join(HERE, "deal-registration.deckcraft")
PNG_DIR = os.path.join(HERE, "slides")
os.makedirs(PNG_DIR, exist_ok=True)

slides = []


def slide(fn):
    slides.append(fn)
    return fn


# 1. Title
@slide
def s_title(s):
    s.add("design.background", {"color": NAVY})
    s.box([60, 150, 70, 8], fill=SAND, preset="rect")
    s.text([56, 170, 840, 80], "Deal Registration, Made Simple", size=44, bold=True, color=WHITE)
    s.text(
        [58, 250, 840, 40],
        "How it works in general, and where our portal fits in",
        size=22,
        color="#B9D4E0",
    )
    s.text(
        [58, 440, 840, 30],
        "DBGI Project Registration Portal  |  Learning guide  |  2026-10-26",
        size=14,
        color="#8FB3C4",
    )


# 2. The problem
@slide
def s_problem(s):
    s.header(
        "The problem: everyone chases the same customer",
        "Without rules, three dealers hear about one buyer and fight over it",
    )
    for i, name in enumerate(["Dealer A", "Dealer B", "Dealer C"]):
        y = 160 + i * 110
        s.box([60, y, 190, 70], name, fill=TEAL, size=18, color=WHITE, bold=True)
        s.icon("briefcase", [76, y + 24, 22, 22], WHITE)
        s.arrow(250, y + 35, 400, 290, color=CORAL, width=3)
    s.box(
        [400, 230, 210, 120],
        "Pasig City Hall\nneeds 20 printers",
        fill=LIGHT,
        line=NAVY,
        size=17,
        color=NAVY,
        bold=True,
    )
    s.icon("building", [490, 196, 30, 30], NAVY)
    s.note(
        [660, 165, 250, 62],
        "Price war: each dealer asks for a bigger discount",
        fill="#FDE8E1",
        color="#9B2915",
        icon="triangle-alert",
    )
    s.note(
        [660, 259, 250, 62],
        "Wasted effort: three teams do the same work",
        fill="#FDE8E1",
        color="#9B2915",
        icon="triangle-alert",
    )
    s.note(
        [660, 353, 250, 62],
        "Unfair: the dealer who found it may lose it",
        fill="#FDE8E1",
        color="#9B2915",
        icon="triangle-alert",
    )
    s.text(
        [60, 470, 850, 40],
        "Result: dealers stop looking for new customers, because someone else may take the reward.",
        size=15,
        color=MUTED,
    )


# 3. The fix
@slide
def s_fix(s):
    s.header(
        "The fix: register first, get protected",
        "The dealer who finds a real deal tells DBGI first, and DBGI protects it",
    )
    s.box(
        [60, 170, 200, 90], "Dealer A\nfinds the deal", fill=TEAL, size=17, color=WHITE, bold=True
    )
    s.arrow(260, 215, 360, 215, color=NAVY, width=3)
    s.text([262, 180, 100, 30], "registers", size=13, color=MUTED, align="center")
    s.box(
        [360, 170, 200, 90], "DBGI\nchecks and approves", fill=NAVY, size=17, color=WHITE, bold=True
    )
    s.arrow(560, 215, 660, 215, color=NAVY, width=3)
    s.box(
        [660, 150, 250, 130],
        "Dealer A gets:\n- Priority on this deal\n- A special price\n- For a limited time",
        fill="#E3F4EC",
        line=GREEN,
        size=16,
        color="#1D6B48",
        bold=False,
        align="left",
    )
    s.add("format.margins", {"left": 18})
    s.box(
        [60, 340, 200, 70],
        "Dealer B",
        fill="#D5DDE3",
        size=17,
        color=MUTED,
        bold=True,
        align="left",
    )
    s.add("format.margins", {"left": 24})
    s.box(
        [60, 425, 200, 70],
        "Dealer C",
        fill="#D5DDE3",
        size=17,
        color=MUTED,
        bold=True,
        align="left",
    )
    s.add("format.margins", {"left": 24})
    s.icon("lock", [222, 362, 24, 24], MUTED)
    s.icon("lock", [222, 447, 24, 24], MUTED)
    s.note(
        [300, 360, 610, 110],
        "Other dealers cannot take the protected deal by undercutting. They can still sell to other customers, or register their own deals.",
        size=16,
    )


# 4. The four players
@slide
def s_players(s):
    s.header("The four players", "Who is involved, and what each one is called in our portal")
    cards = [
        (
            "building",
            "DBGI",
            "Owns the product and the pricing. Decides who gets protection and price.",
            "DBGI administrators",
            NAVY,
        ),
        (
            "briefcase",
            "Dealer / Partner",
            "Finds the buyer and sells to them. Registers the deal.",
            "Company users",
            TEAL,
        ),
        (
            "users",
            "End-user",
            "The actual buyer. Often a government office, like Pasig City Hall.",
            "End-user",
            MINT,
        ),
        (
            "target",
            "Competitors",
            "Other brands the buyer is considering. Helps DBGI judge the price needed to win.",
            "Canon, Epson, HP, Lexmark",
            CORAL,
        ),
    ]
    for i, (icon, name, desc, app, col) in enumerate(cards):
        x = 60 + i * 215
        s.box([x, 140, 200, 270], fill=WHITE, line="#C9D6DE", preset="rect")
        s.box([x, 140, 200, 8], fill=col, preset="rect")
        s.box([x + 74, 166, 52, 52], fill=col, preset="ellipse")
        s.icon(icon, [x + 86, 178, 28, 28], WHITE)
        s.text([x + 10, 230, 180, 34], name, size=18, bold=True, color=NAVY, align="center")
        s.text([x + 14, 266, 172, 80], desc, size=13, color=INK, align="center")
        s.box([x + 14, 358, 172, 38], app, fill=LIGHT, size=12, color=NAVY, bold=True)
    s.text(
        [60, 430, 850, 30],
        "The shaded label at the bottom of each card is that player's name in our portal.",
        size=13,
        color=MUTED,
    )


# 5. The flow
@slide
def s_flow(s):
    s.header(
        "The whole flow in 8 steps",
        "Almost every company that does deal registration follows this shape",
    )
    steps = [
        ("Find", "Dealer learns of a real buying need", TEAL),
        ("Register", "Dealer submits details and proof", TEAL),
        ("Check", "Real? Specific? Duplicate?", NAVY),
        ("Decide", "Approve or reject, set who is first", NAVY),
        ("Price", "DBGI approves a special price", NAVY),
        ("Protect", "Approval lasts a set time", NAVY),
        ("Close", "Dealer wins or loses the sale", TEAL),
        ("Verify order", "DBGI checks the order matches", NAVY),
    ]
    for i, (name, desc, col) in enumerate(steps):
        row, colx = divmod(i, 4)
        x = 60 + colx * 222
        y = 145 + row * 160
        s.box([x, y, 190, 120], fill=WHITE, line=col, line_width=2)
        s.box(
            [x + 12, y + 12, 34, 34],
            str(i + 1),
            fill=col,
            preset="ellipse",
            size=16,
            color=WHITE,
            bold=True,
        )
        s.text([x + 52, y + 14, 134, 30], name, size=17, bold=True, color=col)
        s.text([x + 12, y + 54, 170, 60], desc, size=13, color=INK)
        if colx < 3:
            s.arrow(x + 190, y + 60, x + 222, y + 60, color=MUTED, width=2)
    s.box([60, 470, 18, 18], fill=TEAL, preset="roundRect")
    s.text([84, 466, 200, 26], "Dealer does it", size=13, color=INK)
    s.box([240, 470, 18, 18], fill=NAVY, preset="roundRect")
    s.text([264, 466, 200, 26], "DBGI does it", size=13, color=INK)


# 6. Who is first
@slide
def s_first(s):
    s.header(
        "Steps 3 and 4: who gets the deal?", "Example: three dealers registered the same Pasig deal"
    )
    s.box([60, 200, 850, 4], fill="#C9D6DE", preset="rect")
    rows = [
        (
            120,
            "Sep 28",
            "Dealer C",
            '"Pasig might buy printers soon."\nNo customer contact, no product, no quantity.',
            "Too vague: asked for details",
            CORAL,
        ),
        (
            400,
            "Oct 1",
            "Dealer A",
            "Pasig City Hall, 20 printers, model listed, notice attached.",
            "Rank 1",
            GREEN,
        ),
        (680, "Oct 3", "Dealer B", "Same deal, also specific, with proof.", "Rank 2", TEAL),
    ]
    for x, date, who, what, verdict, col in rows:
        s.box([x + 103, 190, 24, 24], fill=col, preset="ellipse")
        s.text([x + 45, 150, 140, 30], date, size=16, bold=True, color=NAVY, align="center")
        s.box([x, 235, 230, 150], fill=WHITE, line="#C9D6DE")
        s.text([x + 14, 245, 200, 28], who, size=17, bold=True, color=NAVY)
        s.text([x + 14, 275, 205, 100], what, size=13, color=INK)
        s.box([x, 395, 230, 40], verdict, fill=col, size=15, color=WHITE, bold=True)
    s.note(
        [60, 455, 850, 50],
        "Usual rule: the first claim that is real AND specific wins. DBGI's policy decides exactly how strict to be.",
        icon="lightbulb",
        size=15,
    )


# 7. Two separate yes
@slide
def s_two_yes(s):
    s.header(
        "Two separate approvals",
        '"This deal is yours" and "you get this price" are different decisions',
    )
    s.box([60, 140, 410, 300], fill=WHITE, line=NAVY, line_width=2, preset="rect")
    s.box(
        [60, 140, 410, 56],
        "1. Registration approval",
        fill=NAVY,
        size=19,
        color=WHITE,
        bold=True,
        preset="rect",
    )
    s.text([80, 210, 370, 30], "Question: Is this deal yours?", size=16, bold=True, color=NAVY)
    s.text(
        [80, 245, 370, 190],
        "- Is it a real, specific opportunity?\n- Is it a duplicate?\n- Who registered first?\n\nResult: approved or rejected, and a rank (1st, 2nd...)",
        size=15,
        color=INK,
    )
    s.box([500, 140, 410, 300], fill=WHITE, line=TEAL, line_width=2, preset="rect")
    s.box(
        [500, 140, 410, 56],
        "2. Price approval",
        fill=TEAL,
        size=19,
        color=WHITE,
        bold=True,
        preset="rect",
    )
    s.text([520, 210, 370, 30], "Question: What price can you get?", size=16, bold=True, color=TEAL)
    s.text([520, 245, 370, 60], "Example for one printer:", size=15, color=INK)
    prices = [
        ("List price", "PHP 10,000", MUTED),
        ("Dealer requested", "PHP 9,000", CORAL),
        ("DBGI approved", "PHP 9,200", GREEN),
    ]
    for i, (label, val, col) in enumerate(prices):
        y = 275 + i * 46
        s.text([520, y, 200, 34], label, size=15, color=INK, anchor="middle")
        s.box([720, y, 170, 36], val, fill=col, size=15, color=WHITE, bold=True)
        s.add("format.align", {"align": "right"})
        s.add("format.margins", {"right": 14})
    s.note(
        [60, 458, 850, 50],
        "Remember: a requested price is never an approved price. The dealer asks, DBGI decides.",
        icon="circle-alert",
        size=15,
    )


# 8. Protection period
@slide
def s_protect(s):
    s.header("Protection does not last forever", 'Approvals expire, so nobody can "park" a deal')
    s.text([60, 140, 300, 28], "Normal approval", size=16, bold=True, color=NAVY)
    s.box(
        [60, 175, 600, 44],
        "30 days of protection and special price",
        fill=TEAL,
        size=15,
        color=WHITE,
        bold=True,
    )
    s.box([660, 175, 250, 44], "Expired", fill="#D5DDE3", size=15, color=MUTED, bold=True)
    s.text([60, 222, 200, 24], "Approved", size=12, color=MUTED)
    s.text([600, 222, 120, 24], "Expiry date", size=12, color=MUTED, align="center")

    s.text([60, 265, 400, 28], "Renewed BEFORE expiry", size=16, bold=True, color=NAVY)
    s.box([60, 300, 400, 44], "First 30 days", fill=TEAL, size=15, color=WHITE, bold=True)
    s.box(
        [460, 300, 400, 44],
        "+30 days added to the old expiry",
        fill=GREEN,
        size=15,
        color=WHITE,
        bold=True,
    )
    s.text(
        [60, 347, 600, 24], "No gap: protection continues without a break.", size=12, color=MUTED
    )

    s.text([60, 385, 400, 28], "Renewed AFTER expiry", size=16, bold=True, color=NAVY)
    s.box([60, 420, 300, 44], "First 30 days", fill=TEAL, size=15, color=WHITE, bold=True)
    s.box(
        [360, 420, 160, 44],
        "Gap: not covered",
        fill="#FDE8E1",
        line=CORAL,
        size=14,
        color="#9B2915",
        bold=True,
    )
    s.box(
        [520, 420, 390, 44],
        "+30 days from the approval date",
        fill=GREEN,
        size=15,
        color=WHITE,
        bold=True,
    )
    s.text(
        [60, 467, 850, 24],
        "Orders during the gap do not get the special price. Our portal uses +30 days per renewal.",
        size=12,
        color=MUTED,
    )


# 9. Order verification
@slide
def s_verify(s):
    s.header(
        "Step 8: checking the order",
        "Before honoring the special price, DBGI checks the order matches the approved deal",
    )
    s.box(
        [60, 170, 200, 110], "Dealer orders\nfrom DBGI", fill=TEAL, size=18, color=WHITE, bold=True
    )
    s.icon("file-text", [146, 140, 28, 28], TEAL)
    s.arrow(260, 225, 320, 225, color=NAVY, width=3)
    checks = [
        "Same dealer company",
        "Same End-user",
        "Same product",
        "Order date inside the approval period",
        "Approval still active",
    ]
    s.box([320, 140, 330, 300], fill=WHITE, line="#C9D6DE")
    s.text([340, 150, 300, 28], "All five must match", size=16, bold=True, color=NAVY)
    for i, t in enumerate(checks):
        y = 190 + i * 48
        s.box([340, y, 30, 30], fill="#E3F4EC", preset="ellipse")
        s.icon("check", [345, y + 5, 20, 20], GREEN)
        s.text([380, y, 260, 32], t, size=14, color=INK, anchor="middle")
    s.arrow(650, 225, 700, 225, color=GREEN, width=3)
    s.box(
        [700, 170, 210, 110],
        "All match:\nspecial price applies",
        fill="#E3F4EC",
        line=GREEN,
        size=16,
        color="#1D6B48",
        bold=True,
    )
    s.arrow(650, 380, 700, 380, color=CORAL, width=3)
    s.box(
        [700, 330, 210, 110],
        "Any mismatch:\nDBGI reviews first",
        fill="#FDE8E1",
        line=CORAL,
        size=16,
        color="#9B2915",
        bold=True,
    )
    s.note(
        [60, 460, 850, 46],
        "This stops a discount approved for Pasig from being used on a different customer.",
        icon="lock",
        size=15,
    )


# 10. Privacy
@slide
def s_privacy(s):
    s.header("Dealers never see each other's deals", "If they could, the whole system would break")
    s.box(
        [60, 150, 850, 90],
        "DBGI sees everything: all dealers, all deals, all prices, all rankings",
        fill=NAVY,
        size=18,
        color=WHITE,
        bold=True,
        align="left",
    )
    s.add("format.margins", {"left": 66})
    s.icon("search", [86, 182, 26, 26], WHITE)
    s.text([60, 252, 850, 26], "Each dealer is walled off from the others:", size=14, color=MUTED)
    for i, name in enumerate(["Dealer A", "Dealer B", "Dealer C"]):
        x = 60 + i * 290
        s.box([x, 290, 270, 130], fill=WHITE, line=TEAL, line_width=2)
        s.text([x + 16, 300, 200, 30], name, size=18, bold=True, color=TEAL)
        s.icon("lock", [x + 230, 302, 24, 24], TEAL)
        s.text(
            [x + 16, 335, 240, 100],
            "Sees only its own registrations, prices, evidence, and its own rank",
            size=14,
            color=INK,
        )
    s.note(
        [60, 458, 850, 46],
        "Our portal enforces this on the server, not just by hiding buttons on screen.",
        icon="circle-check",
        size=15,
    )


# 11. Glossary table
@slide
def s_glossary(s):
    s.header("Words you will hear at work", "The portal's terms in plain language")
    rows = [
        ("Term", "Plain meaning"),
        ("Matching", "Checking whether two registrations are really the same deal"),
        ("Opportunity / scope", "The one real deal that several registrations point to"),
        ("Rank", "Who is first, second, and so on for that deal"),
        ("Commercial approval", "The price decision"),
        ("Renewal", "Extending an approval (+30 days in our portal)"),
        ("Reorder", "The buyer orders more later: can the approved price be reused?"),
        ("Withdrawal", "The dealer says: I am no longer pursuing this deal"),
        ("Merge / split", "DBGI fixes mistakes: two that are one deal, or one that is two"),
        ("Evidence", "Proof the deal is real, like a procurement notice"),
    ]
    s.add("insert.table", {"rows": len(rows), "cols": 2, "rect": [60, 130, 850, 340]})
    s.add("table.style", {"style": "medium2-accent1"})
    for r, (a, b) in enumerate(rows):
        s.add("text.set", {"text": a, "cell": [r, 0]})
        s.add("text.set", {"text": b, "cell": [r, 1]})
    s.add("text.exit")
    s.add("format.size", {"size": 15})
    s.add("table.cellAlign", {"anchor": "middle"})
    s.add("table.columnWidth", {"col": 0, "width": 230})
    s.add("table.columnWidth", {"col": 1, "width": 620})


# 12. Where the portal is
@slide
def s_status(s):
    s.header(
        "The simple version, and where our portal is today",
        "Six steps are enough to keep deal registration fair and correct",
    )
    items = [
        ("Dealer registers the deal with proof", True),
        ("DBGI checks duplicates and who was first", True),
        ("DBGI approves or rejects the registration", True),
        ("DBGI approves a price separately, with an expiry", True),
        ("DBGI checks each order before applying the price", False),
        ("Dealers cannot see each other's deals", True),
    ]
    for i, (t, done) in enumerate(items):
        y = 140 + i * 52
        s.box(
            [60, y, 40, 40],
            str(i + 1),
            fill=NAVY,
            preset="ellipse",
            size=16,
            color=WHITE,
            bold=True,
        )
        s.box([112, y, 600, 40], t, fill=WHITE, line="#C9D6DE", size=15, color=INK, align="left")
        s.add("format.margins", {"left": 14})
        if done:
            s.box(
                [724, y, 186, 40],
                "Done in portal",
                fill="#E3F4EC",
                size=14,
                color="#1D6B48",
                bold=True,
            )
        else:
            s.box(
                [724, y, 186, 40],
                "Not yet (Milestone 3)",
                fill="#FDF1D6",
                size=14,
                color="#8A5A00",
                bold=True,
            )
    s.note(
        [60, 460, 850, 46],
        "Also still missing: withdrawal requests, and merge or split of deals.",
        icon="info",
        size=15,
    )


# 13. Questions to ask
@slide
def s_questions(s):
    s.header("Questions to ask your team", "These are the decisions the portal is waiting on")
    qs = [
        ("clock", "How long does an approval last, and how do renewals work?"),
        ("flag", "When two dealers register the same deal, what decides who is first?"),
        ("file-text", "Can a dealer edit a registration after submitting it?"),
        ("undo-2", "If a dealer withdraws, does the next dealer move up?"),
        (
            "chart-pie",
            "How are discounts calculated: with or without VAT, and how is rounding done?",
        ),
    ]
    for i, (icon, q) in enumerate(qs):
        y = 140 + i * 66
        s.box([60, y, 54, 54], fill=TEAL, preset="ellipse")
        s.icon(icon, [74, y + 14, 26, 26], WHITE)
        s.box([128, y, 782, 54], q, fill=LIGHT, size=16, color=NAVY, align="left")
        s.add("format.margins", {"left": 18})


# 14. One sentence summary
@slide
def s_summary(s):
    s.add("design.background", {"color": NAVY})
    s.box([60, 140, 70, 8], fill=SAND, preset="rect")
    s.text([56, 160, 840, 40], "Deal registration in one sentence", size=22, color="#B9D4E0")
    s.text(
        [56, 205, 850, 200],
        "The dealer who finds a real deal first registers it. DBGI confirms it, protects it for a limited time with a special price, and checks the order before honoring that price.",
        size=28,
        bold=True,
        color=WHITE,
    )


def build(only=None):
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
        run(s.cmds, src=src, save=OUT)
    s = Slide()
    s.add("design.headerFooter", {"slideNumber": True, "hideOnTitle": True, "all": True})
    run(s.cmds, src=OUT, save=OUT)
    for i in range(len(slides)):
        if only is None or i in only:
            run(
                [c("slide.go", {"index": i})],
                src=OUT,
                export=os.path.join(PNG_DIR, f"slide-{i + 1:02d}.png"),
                export_params={"slide": i},
            )
    print(f"built {len(slides)} slides -> {OUT}")


if __name__ == "__main__":
    build()
