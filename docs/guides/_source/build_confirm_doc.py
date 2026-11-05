"""Build "Portal Rules to Confirm" (.docx): docs/PORTAL_RULES.md section 16 as a plain-English form.

Written for the head of pricing and business development. Uses real Word check boxes and text boxes, so it can
be filled in on screen.
"""

import os

from build_decisions_doc import OUT_DIR
from doclib import NAVY, TEXT_WIDTH, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "Portal Rules to Confirm.docx")
TITLE = "Portal Rules to Confirm"

KEEP = "Yes, keep this"
CHANGE = "No, change it (please write how below)"

GROUPS = [
    (
        "1. When a partner changes a deal",
        "A partner can edit a deal after sending it. These questions are about which changes DBGI needs to check.",
        [
            {
                "q": "Can partners fix small details without DBGI checking?",
                "now": "Yes. These need no check: the contact person, position, email, and phone number; notes about a "
                "competitor; the reason given for a price; and fixes to only capital letters, punctuation, or spacing "
                "in the project title or the attachment description. The deal keeps its status and its place in line. "
                "The change is still saved in the deal's history.",
                "example": "A partner typed a wrong phone number and fixes it. DBGI does not need to do anything.",
            },
            {
                "q": "Can they still fix small details after DBGI starts checking the price?",
                "now": "Yes. But the products, quantities, and requested prices stay locked.",
                "example": "DBGI is checking the price. The partner can change the contact person, but cannot change "
                "the quantity.",
            },
            {
                "q": "Which changes must DBGI check?",
                "now": "These must go back to DBGI: the buyer (end-user), project title, bid date, delivery date, "
                "attachment description and link, the competitor's brand, model, or price, the products, quantities, "
                "and requested prices, and a request to use today's list price. The deal keeps its place in line.",
                "example": "The partner moves the bid date to next month. DBGI must check the deal again.",
            },
            {
                "q": "Should DBGI be told when a partner changes attachment files on a confirmed deal?",
                "now": "Yes. If DBGI already confirmed the deal (status Registered), and the partner adds, replaces, or "
                "removes a file, the deal is marked for review and DBGI gets a portal message and an email. A DBGI "
                "system administrator can turn this off in the portal settings. If DBGI has not confirmed the deal yet, "
                "there is no separate message, because DBGI will see the files during its review.",
                "example": "A partner replaces the request for quotation on a Registered deal. DBGI gets a message.",
            },
        ],
    ),
    (
        "2. What happens to the price when a deal changes",
        "When a partner sends a deal, the portal saves the list price of that day. These questions are about when "
        "that saved price should change.",
        [
            {
                "q": "Should editing a deal change its price?",
                "now": "No, unless the edit changes what is being priced. Products that were not touched keep their "
                "saved price.",
                "example": "The saved list price is 10,000. DBGI later raises the list price to 11,000. The partner "
                "fixes a phone number. The saved price stays 10,000.",
            },
            {
                "q": "What if only the quantity changes?",
                "now": "The price for each piece stays the same, and the total is worked out again. DBGI checks the change.",
                "example": "The partner changes 20 printers to 25 at 9,000 each. The total goes from 180,000 to 225,000.",
            },
            {
                "q": "What if a product is added or changed?",
                "now": "Only that product takes today's list price. The other products keep their saved price.",
                "example": "A deal has a printer at the old price. The partner adds a scanner. Only the scanner uses "
                "today's price.",
            },
            {
                "q": "What if the buyer or the dates change?",
                "now": "The price stays the same. DBGI checks the change, and can choose to apply today's prices.",
                "example": "The delivery date moves by one month. The price stays, unless DBGI decides to update it.",
            },
            {
                "q": "Can a partner ask for today's list price?",
                "now": "Yes. The partner ticks a box when editing the deal. All products from the product list take "
                "today's price, and DBGI checks it.",
                "example": "The list price went down. The partner ticks the box to ask for the lower price.",
            },
            {
                "q": "Can DBGI apply today's list price by itself?",
                "now": "Yes, if DBGI writes a reason and the price check has not started yet. The partner gets a message.",
                "example": "The list price changed before DBGI started checking the price, so DBGI updates the deal.",
            },
        ],
    ),
    (
        "3. Details we chose while building your decisions",
        "You already decided these rules. We had to choose some small details to make them work, so please check them.",
        [
            {
                "q": "Which deals does the 60-day limit cover?",
                "now": "Only deals DBGI has not confirmed yet. We count from the day the partner sent the deal. Deals "
                "that are already confirmed are not covered.",
                "example": "A deal is still waiting for DBGI after 60 days, so it goes back to DBGI's review list.",
            },
            {
                "q": "How does the portal know a tender was postponed or posted again?",
                "now": "A DBGI staff member sets the project to On hold. This starts the 60 days. If nobody sets it to "
                "On hold, the 60 days do not start.",
                "example": "The city postpones its bidding. DBGI sets the project to On hold, and the partners keep "
                "their places for 60 days.",
            },
            {
                "q": "When should DBGI staff get an email?",
                "now": "For a new deal, corrections sent by a partner, a change after a deal was confirmed, a report "
                "that a project was won or lost, a 60-day limit being reached, and a request to renew a price. When a "
                "partner withdraws a deal, DBGI gets only a portal message, because no action is needed.",
                "example": "A partner asks to renew a price. DBGI gets a portal message and an email.",
            },
            {
                "q": "When DBGI decides a tie, should the companies get different ranks?",
                "now": "Yes. DBGI sets a final order, so the companies get different ranks. The other choice is to keep "
                "their rank the same and only write down DBGI's decision.",
                "example": "Two companies tie for first place. After DBGI decides, one is rank 1 and the other is rank 2.",
                "choices": [
                    "Yes, keep this: different ranks",
                    "No, keep the same rank and only write down the decision",
                    "Something else (please write below)",
                ],
            },
            {
                "q": "Can a product not on our list join a group of products whose price is already decided?",
                "now": "Not right away. DBGI must first ask for changes on that price decision. Then the new product "
                "can be added, and the price is checked again.",
                "example": "DBGI approved the price for a deal's printers. A partner's typed-in printer is then added to "
                "the product list. DBGI must reopen the printer price decision first.",
            },
        ],
    ),
    (
        "4. Repeat orders, merges, and splits",
        "You already decided these rules, and they are now built. We chose these details while building them.",
        [
            {
                "q": "Can a partner ask for a repeat order after the approved price has ended?",
                "now": "No. The partner must renew the price first. DBGI also cannot accept a waiting repeat order "
                "after the price has ended.",
                "example": "The price ended last week. The partner asks to renew it, then sends the repeat order.",
            },
            {
                "q": "Should there be a limit on repeat orders?",
                "now": "No. A partner can send any number of repeat orders, for any quantity, until the price ends. "
                "DBGI checks each one.",
                "example": "The city orders 5 more printers in March and 10 more in April. Both can ask for the same price.",
            },
            {
                "q": "When two projects are merged, who gets first place?",
                "now": "The earliest original submission time gets first place, and each company counts once. DBGI can "
                "change the order for that case and must write a reason.",
                "example": "Company A sent its deal on Monday and Company B on Tuesday. After the merge, A is rank 1 and "
                "B is rank 2, unless DBGI decides differently.",
            },
            {
                "q": "What happens to decided prices when projects merge or a deal is split?",
                "now": "DBGI chooses each time: keep the prices, or send them back to be checked again.",
                "example": "A deal with an approved price moves to the merged project. DBGI keeps the price.",
            },
            {
                "q": "When a deal is split, does the new deal keep its place in line?",
                "now": "Yes. The new deal is for the same company and keeps the original submission time.",
                "example": "A deal covers two lots. DBGI moves the second lot to a new deal, and it keeps Monday's time.",
            },
        ],
    ),
]


def label(doc, name, text):
    doc.start("Normal")
    doc.c("para.keepNext")
    doc.c("para.set", {"props": {"spaceAfter": 4}})
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": f"{name}: "})
    doc.c("format.resetChar")
    doc.runs(text)
    doc.c("text.newParagraph")


def answer_table(doc, number, choices):
    """Rows of a real check box and its text, then a row for notes."""
    doc.start("Normal")
    doc.c("insert.table", {"rows": len(choices) + 1, "cols": 2, "style": "TableGrid"})
    doc.c("table.autofit", {"mode": "fixed"})
    for row, choice in enumerate(choices):
        if row:
            doc.c("text.tab")
        # Keeps the whole answer box on one page
        doc.c("para.keepNext")
        if row == 0:
            doc.c("table.columnWidth", {"width": 48})
        doc.c(
            "developer.checkBox",
            {"title": f"Question {number}: {choice}", "tag": f"q{number}-{row + 1}"},
        )
        doc.c("text.tab")
        if row == 0:
            doc.c("table.columnWidth", {"width": TEXT_WIDTH - 48})
        doc.c("para.keepNext")
        doc.c("text.insert", {"text": choice})
    doc.c("text.tab")
    doc.c("text.insert", {"text": "Notes"})
    doc.c("text.tab")
    doc.c("developer.richText", {"title": f"Question {number} notes", "tag": f"q{number}-notes"})
    doc.c("caret.docEnd")
    doc.after_table = True


def build():
    doc = Doc()
    doc.c("file.properties", {"title": TITLE})
    doc.title(TITLE, "Please check how these rules work")
    doc.para(
        "These rules already work in the portal, but you have not seen them yet. Please check that each one is right. "
        "If one is wrong, tell us and we will change the portal."
    )
    doc.para(
        "**How to answer:** click one box for each question. If you want to add something, click beside **Notes** "
        "and type. You can fill this in on your computer."
    )
    doc.callout("There are 20 questions. Each one has a short example.")
    number = 0
    for title, intro, items in GROUPS:
        doc.h1(title)
        doc.para(intro)
        for item in items:
            number += 1
            doc.h2(f"{number}. {item['q']}")
            label(doc, "What the portal does now", item["now"])
            label(doc, "Example", item["example"])
            answer_table(doc, number, item.get("choices", [KEEP, CHANGE]))
    doc.h1("When you are done")
    doc.para(
        "Please save this file and send it back. We will update the portal to match your answers."
    )
    doc.start("Normal")
    doc.c("insert.table", {"rows": 2, "cols": 2, "style": "TableGrid"})
    doc.c("table.autofit", {"mode": "fixed"})
    doc.c("table.columnWidth", {"width": 110})
    doc.c("text.insert", {"text": "Answered by"})
    doc.c("text.tab")
    doc.c("table.columnWidth", {"width": TEXT_WIDTH - 110})
    doc.c("developer.plainText", {"title": "Answered by", "tag": "answered-by"})
    doc.c("text.tab")
    doc.c("text.insert", {"text": "Date"})
    doc.c("text.tab")
    doc.c("developer.datePicker", {"title": "Date", "tag": "answered-date", "format": "yyyy-MM-dd"})
    doc.c("caret.docEnd")
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = doc.save(OUT)
    preview = os.path.join(HERE, "decision-pages")
    os.makedirs(preview, exist_ok=True)
    for page in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"confirm-{page:02d}.png"), page=page, scale=0.8)
    assert number == 20, number
    print(f"{number} questions, {pages} pages -> {OUT}")
    return pages


if __name__ == "__main__":
    build()
