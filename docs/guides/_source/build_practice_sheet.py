"""Build "Practice Sheet" (.docx): hands-on steps for colleagues after the portal presentation.

Plain English, company accounts only. Three pairs ran these steps at once on the test server on 2026-11-05.
Uses real Word check boxes and text boxes, so it can be filled in on screen.
"""

import os

from doclib import MUTED, NAVY, TEXT_WIDTH, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "Portal User Guide 2026-11", "Practice Sheet.docx"))
TITLE = "Practice the DBGI Portal"
ADDRESS = "http://187.127.124.78:8081"

STEPS = [
    (
        "Your company",
        "Click **New registration**. Choose **your pair's end-user**. Add a competitor, then product **M1820W**, "
        "quantity 20, price 9000. Describe your proof, tick the box, and click **Create registration**.",
        "9 to 12",
    ),
    (
        "DBGI",
        "Click **Portal**, then open the deal. Type a reason and click **Start review**. Choose **Create a new whole "
        "opportunity**, type a reason, and click the button at the bottom.",
        "18 to 23",
    ),
    (
        "DBGI",
        "Click **Administration**, then **Price approvals**, and open the deal. Set Status to **Approved** and type a "
        "reason. Click **Add another**, choose the product, type **8000**, and click **Save**.",
        "25, 26",
    ),
    (
        "Your company",
        "Open your deal and find the approved price. Click **Rankings**. You should be **rank 1**.",
        "27, 30",
    ),
    (
        "Other company",
        "Register the same project: same end-user, same product. It should say **Registered**, because the portal "
        "matched it. If it says **Submitted**, review it as DBGI and choose **Link to an existing opportunity**.",
        "9 to 12, 24",
    ),
    (
        "DBGI",
        "Approve the other company's price at **8000**, the same as rank 1. Read the warning. Then open it again and "
        "change the price to **8500**.",
        "26",
    ),
    (
        "Other company",
        "Click **Rankings**. You should be **rank 2**, and you cannot see the other company.",
        "30",
    ),
    (
        "Your company, then DBGI",
        "On your deal, click **Request renewal** and send a reason. As DBGI, open the deal and click **Approve**. Check "
        "that the end date moved by 30 days.",
        "28, 29",
    ),
    (
        "Your company, then DBGI",
        "Click **Report project outcome**, choose **Won**, and send it. As DBGI, open the deal and confirm it.",
        "35, 36",
    ),
]


def steps_table(doc):
    rows = len(STEPS) + 1
    widths = [40, 74, TEXT_WIDTH - 40 - 74 - 56, 56]
    doc.start("Normal")
    doc.c("insert.table", {"rows": rows, "cols": 4, "style": "GridTable4AccentBlue"})
    doc.c("table.autofit", {"mode": "fixed"})
    for col, heading in enumerate(("Done", "Who", "What to do", "Slides")):
        if col:
            doc.c("text.tab")
        doc.c("table.columnWidth", {"width": widths[col]})
        doc.c("text.insert", {"text": heading})
    for number, (who, what, slides) in enumerate(STEPS, start=1):
        doc.c("text.tab")
        doc.c("developer.checkBox", {"title": f"Step {number} done", "tag": f"step-{number}"})
        doc.c("text.tab")
        doc.c("text.insert", {"text": who})
        doc.c("text.tab")
        doc.runs(what)
        doc.c("text.tab")
        doc.c("text.insert", {"text": slides})
    doc.c("caret.docEnd")
    doc.after_table = True


def feedback_table(doc):
    questions = (
        ("What confused you?", "confusing"),
        ("What is missing, or does not match how you work?", "missing"),
        ("Your name", "name"),
    )
    doc.start("Normal")
    doc.c("insert.table", {"rows": len(questions), "cols": 2, "style": "TableGrid"})
    doc.c("table.autofit", {"mode": "fixed"})
    doc.c("table.columnWidth", {"width": 170})
    for row, (question, tag) in enumerate(questions):
        if row:
            doc.c("text.tab")
        doc.c("text.insert", {"text": question})
        doc.c("text.tab")
        if row == 0:
            doc.c("table.columnWidth", {"width": TEXT_WIDTH - 170})
        doc.c("developer.richText", {"title": question, "tag": tag})
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
    doc.c("text.insert", {"text": "Try it yourself, with the slides beside you"})
    doc.c("format.resetChar")
    doc.c("text.newParagraph")
    doc.warn(
        "**This is a test copy.** Use made-up prices only. Do not upload real documents or use a real password here. "
        "Other people can see what you enter, and it may be deleted at any time."
    )
    doc.h2("How to sign in")
    doc.para(
        f"Open **{ADDRESS}**. You will see a list of accounts, not just the sign-in box in the slides. Find **your "
        "pair** at the top of the list. You play both companies in your pair, and DBGI too."
    )
    doc.table(
        [
            ["Pair", "Your company", "Other company", "Your pair's end-user"],
            ["1", "IT Avenue", "Lexmark", "City of Lucena Mayor's Office"],
            ["2", "Fast Max", "Pinoy Hub", "Quezon City Government"],
            ["3", "Techno Pro", "None Can Beat", "City Government of Davao"],
        ],
        [34, 100, 100, TEXT_WIDTH - 234],
    )
    doc.para(
        "Click a card to sign in as that company. For DBGI, find **DBGI Practice** and click **Portal** or **Django "
        "admin**. If a password is asked for, it is **testpass123**. To change accounts, click **Log out**."
    )
    doc.good(
        "**Stay with your pair's end-user,** and open only its deals. That keeps your test apart from the others."
    )
    doc.h2("Follow one deal")
    steps_table(doc)
    doc.callout(
        "On this test copy, messages appear only inside the portal. No emails go out, and time-limit reminders do not run."
    )
    doc.h2("Tell us what you think")
    doc.para("Please fill this in, save the file, and send it back to the person who shared it.")
    feedback_table(doc)
    pages = doc.save(OUT)
    preview = os.path.join(HERE, "portal-slides", "guide2")
    os.makedirs(preview, exist_ok=True)
    for page in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"practice-{page}.png"), page=page, scale=1.0)
    print(f"{len(STEPS)} steps, {pages} pages -> {OUT}")


if __name__ == "__main__":
    build()
