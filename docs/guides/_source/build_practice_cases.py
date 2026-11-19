"""Build "Practice Sheet - More Cases" (.docx): the other scenarios, after the main Practice Sheet.

Same pairs, sign-in, and layout as build_practice_sheet.py. Each case is a short checklist with slide numbers.
The cases run in order on each pair's own end-user, and some reuse the deals from the first sheet.
Test catalog on the test server: M1820W and P1820W (Laser Printers), DEMO-001 (Demo products).
"""

import os

from build_practice_sheet import ADDRESS, feedback_table
from doclib import MUTED, NAVY, TEXT_WIDTH, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(
    os.path.join(HERE, "..", "Portal User Guide 2026-11", "Practice Sheet - More Cases.docx")
)
TITLE = "Practice More Cases"
CASE_DEAL = "Case practice: printers and scanners"
# WordCraft does not keep a heading with the table after it, so these cases start a new page.
NEW_PAGE = {"2", "5", "8"}

CASES = [
    (
        "1. DBGI asks for changes",
        [
            (
                "Your company",
                "Click **New registration** and choose your pair's end-user. Title: **" + CASE_DEAL + "**. Add a "
                "competitor. Add two products: **P1820W**, quantity 10, price 8500, and **DEMO-001**, quantity 2, "
                "price 4500. Describe your proof, tick the box, and click **Create registration**. It says "
                "**Submitted**.",
                "9 to 12",
            ),
            (
                "DBGI",
                "Open the deal, type a reason, and click **Start review**. Choose **Request changes**, type what to fix "
                "(for example: add the name of the person who sent the request for quotation), and click **Request "
                "changes**.",
                "18 to 20",
            ),
            (
                "Your company",
                "Open the deal. It says **Returned for changes**. Read DBGI's instructions under **Activity**. Click "
                "**Edit registration**, add a name to the attachment description, and click **Save changes**. It says "
                "**Resubmitted**.",
                "21, 22",
            ),
            (
                "DBGI",
                "Start the review again. Choose **Create a new whole opportunity**, type a reason, and click **Create "
                "and link new opportunity**. It says **Registered**.",
                "23, 24",
            ),
        ],
    ),
    (
        "2. Change a confirmed deal",
        [
            (
                "Your company",
                "Open the case deal and click **Edit registration**. Change only the **contact number**, and save. It "
                "stays **Registered**, because this is a small fix.",
                "31, 32",
            ),
            (
                "Your company",
                "Edit it again. Change the P1820W quantity from **10 to 12**, and save. It says **Review required "
                "after edit**. The unit price stays the same, and your place in line does not change.",
                "32, 33",
            ),
            (
                "DBGI",
                "Open the deal and click **Start review**. Choose **Link to an existing opportunity**, pick the case "
                "project, type a reason, and click **Link existing opportunity**. It says **Registered** again.",
                "18, 19",
            ),
        ],
    ),
    (
        "3. Merge two projects",
        [
            (
                "DBGI",
                "Click **Rankings**. Your pair's end-user now has two projects. On the case project, click **Merge**. "
                "In **Merge into**, choose your first project. Read the preview: earliest deal first, each company "
                "once. Keep the prices, type a reason, and click **Merge projects**. This cannot be undone.",
                "43",
            ),
            (
                "Your company",
                "Click **Rankings**. There is one project now, and you are still **rank 1**.",
                "30, 43",
            ),
        ],
    ),
    (
        "4. Split a deal",
        [
            (
                "DBGI",
                "Open the case deal and click **Split deal**. Tick **DEMO-001**, type **Lot 2** as the new lot name, "
                "keep the prices, type a reason, and click **Split deal**. The app opens the new deal.",
                "44",
            ),
            (
                "Your company",
                "Go to your deal list. The case deal is now two deals. The new one has only DEMO-001, and the same "
                "submission time.",
                "7, 44",
            ),
        ],
    ),
    (
        "5. A product not in the catalog",
        [
            (
                "Other company",
                "Click **New registration** and choose your pair's end-user. For the product, choose **Not in "
                "catalog** and type **Wireless presenter**. Quantity 5, price 1200. Finish and click **Create "
                "registration**.",
                "11, 41",
            ),
            (
                "DBGI",
                "Click **Start review**, then choose **Link to an existing opportunity**, pick your pair's project, "
                "type a reason, and click **Link existing opportunity**.",
                "18, 19",
            ),
            (
                "DBGI",
                "Under **Requested products**, click **Add to catalog** on that row. Choose **New product**. Code: "
                "**PRES-** and your pair number (for example PRES-1). Name: Wireless presenter. Category: Accessories. "
                "List price 1500. Type a reason and click **Add to catalog**.",
                "41",
            ),
            (
                "DBGI",
                "A new price review appears under **Commercial approvals**. Click **Decide price** and approve 1200.",
                "25, 26",
            ),
        ],
    ),
    (
        "6. Reject a deal",
        [
            (
                "Other company",
                "Register a new deal for your pair's end-user: product **DEMO-001**, quantity 1, price **100**.",
                "9 to 12",
            ),
            (
                "DBGI",
                "Click **Start review**. Choose **Reject registration**, type why (for example: the price is far below "
                "cost), and click **Reject registration**.",
                "19",
            ),
            (
                "Other company",
                "Open the deal. It says **Rejected**, and DBGI's reason is under **Activity**. A rejected deal cannot "
                "be changed.",
                "15",
            ),
        ],
    ),
    (
        "7. A renewal is declined",
        [
            (
                "Your company",
                "Open your deal from the first sheet. Under **Commercial approvals**, click **Request renewal**, type a "
                "reason, and send it.",
                "28",
            ),
            (
                "DBGI",
                "Open the deal and click **Decline** in the Renewal column. Type a reason. The end date stays the "
                "same.",
                "29",
            ),
        ],
    ),
    (
        "8. Put a project on hold",
        [
            (
                "DBGI",
                "Open any deal on your pair's project and click **Change project status**. Choose **On hold**, type a "
                "reason, and click **Change status**. Every deal on the project now shows On hold.",
                "38",
            ),
            (
                "DBGI",
                "Change the status again, to **Active**. This also undoes the Won from the first sheet, so the next "
                "case works.",
                "38",
            ),
        ],
    ),
    (
        "9. An outcome report is not accepted",
        [
            (
                "Other company",
                "Open your deal from the first sheet and click **Report project outcome**. Choose **Lost**, type what "
                "happened, and click **Send report**.",
                "35",
            ),
            (
                "DBGI",
                "Under **Project outcome reports**, click **Do not accept**. Type a note (for example: please send the "
                "notice of award) and confirm.",
                "36",
            ),
            (
                "Other company",
                "Read DBGI's note. You can send a new report.",
                "36",
            ),
        ],
    ),
    (
        "10. Repeat orders",
        [
            (
                "Your company",
                "Open your deal from the first sheet. Under **Repeat orders**, click **Request repeat order**. Quantity "
                "5. For the **NOA** and **NTP**, choose any made-up PDF or picture, never a real letter. Tick the box "
                "and click **Send request**.",
                "46, 47",
            ),
            (
                "DBGI",
                "Under **Repeat orders**, click **NOA** and **NTP** to open them. Click **Accept**, type a reason, and "
                "confirm.",
                "48",
            ),
            (
                "Your company, then DBGI",
                "Send one more request, with quantity 3. As DBGI, click **Decline** and type why.",
                "47, 48",
            ),
        ],
    ),
    (
        "11. Withdraw a deal",
        [
            (
                "Other company",
                "Open your deal from the first sheet and click **Withdraw registration**. Type a reason and confirm. "
                "This is final: there is no undo.",
                "34",
            ),
            (
                "DBGI",
                "Click **Rankings**. The other company is no longer on your pair's project.",
                "30, 34",
            ),
        ],
    ),
]


def case_table(doc, case_no, steps):
    widths = [40, 74, TEXT_WIDTH - 40 - 74 - 56, 56]
    doc.start("Normal")
    doc.c("insert.table", {"rows": len(steps) + 1, "cols": 4, "style": "GridTable4AccentBlue"})
    doc.c("table.autofit", {"mode": "fixed"})
    for col, heading in enumerate(("Done", "Who", "What to do", "Slides")):
        if col:
            doc.c("text.tab")
        doc.c("table.columnWidth", {"width": widths[col]})
        doc.c("para.keepNext")  # keep each case's table on one page
        doc.c("text.insert", {"text": heading})
    for number, (who, what, slides) in enumerate(steps, start=1):
        keep = number < len(steps)
        cells = [
            lambda: doc.c(
                "developer.checkBox",
                {"title": f"Case {case_no}, step {number} done", "tag": f"case-{case_no}-step-{number}"},
            ),
            lambda: doc.c("text.insert", {"text": who}),
            lambda: doc.runs(what),
            lambda: doc.c("text.insert", {"text": slides}),
        ]
        for fill in cells:
            doc.c("text.tab")
            if keep:
                doc.c("para.keepNext")
            fill()
    doc.c("caret.docEnd")
    doc.after_table = True


def build():
    doc = Doc()
    doc.c("file.properties", {"title": TITLE})
    doc.start("Normal")
    doc.c("format.set", {"props": {"bold": True, "size": 24, "color": NAVY}})
    doc.c("text.insert", {"text": TITLE})
    doc.c("format.resetChar")
    doc.c("text.newParagraph")
    doc.start("Normal")
    doc.c("format.set", {"props": {"size": 12, "color": MUTED}})
    doc.c("text.insert", {"text": "The other things that can happen to a deal"})
    doc.c("format.resetChar")
    doc.c("text.newParagraph")
    doc.warn(
        "**This is a test copy.** Use made-up prices only. Do not upload real documents or use a real password here. "
        "Other people can see what you enter, and it may be deleted at any time."
    )
    doc.h2("Before you start")
    doc.bullets(
        [
            "**Finish the first Practice Sheet first.** Some cases use the deals you made there.",
            f"Sign in the same way: open **{ADDRESS}** and use **your pair's** cards, and **DBGI Practice** for DBGI. "
            "If a password is asked for, it is **testpass123**.",
            "Do the cases **in order**, and stay with **your pair's end-user**.",
            "Cases 1 to 4 use one new deal, called the **case deal**. Cases 7 to 11 use the deals from the first sheet.",
        ]
    )
    for title, steps in CASES:
        if title.split(".")[0] in NEW_PAGE:
            doc.c("text.pageBreak")
        doc.h2(title)
        case_table(doc, title.split(".")[0], steps)
    doc.callout(
        "Not on this test copy: changing a **list price** and **Apply current list prices** (slides 39 and 40). The "
        "catalog is shared by every pair, so a price change would affect everyone."
    )
    doc.h2("Tell us what you think")
    doc.para("Please fill this in, save the file, and send it back to the person who shared it.")
    feedback_table(doc)
    pages = doc.save(OUT)
    preview = os.path.join(HERE, "portal-slides", "guide2")
    os.makedirs(preview, exist_ok=True)
    for page in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"cases-{page}.png"), page=page, scale=1.0)
    print(f"{sum(len(s) for _, s in CASES)} steps in {len(CASES)} cases, {pages} pages -> {OUT}")


if __name__ == "__main__":
    build()
