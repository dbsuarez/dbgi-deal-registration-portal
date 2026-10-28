"""Build the fill-in Word answer form for the DBGI decision questions with wordcraft-cli.

Reads the same docs/DECISIONS_TO_MAKE_*.md as the deck and the printable sheet, so ids and choices match.
Each question gets a drop-down of its choices and a notes box (Word content controls), and the slide number
of that question in the "Using the DBGI Portal" deck.
"""

import os

from build_decisions_doc import OUT_DIR, SOURCE, choices, parse
from build_portal_deck import slides
from doclib import MUTED, NAVY, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "DBGI Portal Answer Form.docx")
WIDTHS = (190, 130, 131)  # question, choice, notes: the 451 pt A4 text width
EXTRA = ["Keep what the portal does today", "Other (see notes)", "Skip, not my area"]


def slide_number(qid):
    names = [fn.__name__ for fn in slides]
    return names.index(f"s_question_{qid}") + 1


def field(doc, label, control, params):
    doc.start("Normal")
    doc.c("para.set", {"props": {"spaceAfter": 8}})
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": f"{label}: "})
    doc.c("format.resetChar")
    doc.c(control, params)
    doc.c("caret.docEnd")
    doc.c("text.newParagraph")


def part_table(doc, part):
    questions = part["questions"]
    doc.start("Normal")
    doc.c("insert.table", {"rows": len(questions) + 1, "cols": 3, "style": "GridTable4AccentBlue"})
    doc.c("table.autofit", {"mode": "fixed"})
    doc.c("table.properties", {"headerRow": True})
    for col, (head, width) in enumerate(zip(("Question", "Your choice", "Notes"), WIDTHS)):
        if col:
            doc.c("text.tab")
        doc.c("table.columnWidth", {"width": width})
        doc.c("text.insert", {"text": head})
    for q in questions:
        qid = q["title"].split(".", 1)[0]
        doc.c("text.tab")
        doc.c("text.insert", {"text": q["title"]})
        doc.c("text.lineBreak")
        doc.c("format.set", {"props": {"bold": False, "size": 8, "color": MUTED}})
        doc.c("text.insert", {"text": f"Explained on slide {slide_number(qid)}"})
        doc.c("format.resetChar")
        doc.c("text.tab")
        options = choices(q.get("choices", ""))
        if options:
            items = [f"{o[1]}: {o[4].upper()}{o[5:]}" for o in options]
            # Skip the extra keep option when a choice already means keeping today's behaviour
            if any(o[4:].lower().startswith("keep") for o in options):
                items += EXTRA[1:]
            else:
                items += EXTRA
            doc.c(
                "developer.dropDown",
                {"title": f"{qid} choice", "tag": f"{qid}-choice", "items": items},
            )
        else:
            doc.c("format.set", {"props": {"italic": True, "size": 9, "color": MUTED}})
            doc.c("text.insert", {"text": "Open question: answer in Notes"})
            doc.c("format.resetChar")
        doc.c("text.tab")
        doc.c("developer.richText", {"title": f"{qid} notes", "tag": f"{qid}-notes"})
    doc.c("caret.docEnd")
    doc.after_table = True


def build():
    parts = parse(SOURCE)
    doc = Doc()
    doc.title("DBGI Portal Answer Form", 'Companion to the "Using the DBGI Portal" slides')
    doc.para(
        "The slides explain each question: what it means, what the portal does today, and the choices. "
        "This form only records your answers, one row per question slide."
    )
    doc.bullets(
        [
            "Open this form in **Microsoft Word** (desktop or online) and the slides beside it. "
            "Each row shows the slide that explains it.",
            "Click **Pick an option** to choose, and **Type here** to add notes or your own rule.",
            "The first choice on each slide is only a suggestion. Skip anything outside your area.",
            "Save the form and send it back to the person who sent you the slides.",
        ]
    )
    field(doc, "Name", "developer.plainText", {"title": "Name", "tag": "name"})
    field(
        doc,
        "Area (sales, pricing, IT, other)",
        "developer.plainText",
        {"title": "Area", "tag": "area"},
    )
    field(
        doc,
        "Date",
        "developer.datePicker",
        {"title": "Date", "tag": "date", "format": "yyyy-MM-dd"},
    )
    for i, part in enumerate(parts):
        if i:
            # Start each later part on a new page from its heading; a separate page-break
            # paragraph spills onto a blank page when the table above fills its page exactly
            doc.start("Heading1")
            doc.c("para.pageBreakBefore", {"value": True})
            doc.c("text.insert", {"text": part["title"]})
            doc.c("text.newParagraph")
        else:
            doc.h1(part["title"])
        part_table(doc, part)
    doc.start("Normal")
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": "Anything else we should know? "})
    doc.c("format.resetChar")
    doc.c("developer.richText", {"title": "Other comments", "tag": "comments"})
    doc.c("caret.docEnd")
    doc.c("text.newParagraph")
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = doc.save(OUT)
    preview = os.path.join(HERE, "decision-pages")
    os.makedirs(preview, exist_ok=True)
    for p in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"form-{p:02d}.png"), page=p, scale=1.0)
    count = sum(len(p["questions"]) for p in parts)
    print(f"{count} questions, {pages} pages -> {OUT}")


if __name__ == "__main__":
    build()
