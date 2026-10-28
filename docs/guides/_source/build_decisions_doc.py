"""Build the printable decision questionnaire from docs/DECISIONS_TO_MAKE_*.md with wordcraft-cli.

The Markdown file stays the single source: each `### ID. Question` with its Means, Today, Ask, Choices,
and Unblocks bullets becomes a block with tick boxes and lines to write on.
"""

import os
import re
import subprocess

from doclib import LIGHT, MUTED, NAVY, TEAL, TEXT_WIDTH, WC, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "..", "..", "DECISIONS_TO_MAKE_2026-10-28.md")
OUT_DIR = os.path.join(HERE, "..", "Decision Questions")
OUT = os.path.join(OUT_DIR, "DBGI Portal Decisions.docx")
BOX = "☐"


def parse(path):
    """Return the intro paragraphs and the parts, each with its questions and their fields."""
    text = open(path, encoding="utf-8").read()
    parts, part, question = [], None, None
    for line in text.splitlines():
        if line.startswith("## Part "):
            part = {"title": line[3:].strip(), "intro": "", "questions": []}
            parts.append(part)
        elif line.startswith("## "):
            part = None
        elif line.startswith("### ") and part is not None:
            question = {"title": line[4:].strip()}
            part["questions"].append(question)
        elif part is not None and (m := re.match(r"- \*\*(\w+):\*\*\s*(.*)", line)):
            question[m.group(1).lower()] = m.group(2).strip()
        elif (
            part is not None
            and not part["questions"]
            and line.strip()
            and not line.startswith("---")
        ):
            part["intro"] += line.strip() + " "
    return parts


def choices(text):
    """Split '(a) first; (b) second.' into ['(a) first', '(b) second']."""
    found = re.findall(r"\(([a-z])\)\s*(.+?)(?=;\s*\([a-z]\)|$)", text)
    return [f"({letter}) {body.strip().rstrip('.;')}" for letter, body in found]


def label(doc, name, text):
    doc.start("Normal")
    doc.c("para.keepNext")
    doc.c("para.set", {"props": {"spaceAfter": 3}})
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": f"{name}: "})
    doc.c("format.resetChar")
    doc.runs(text)
    doc.c("text.newParagraph")


def today(doc, text):
    doc.start("Normal")
    doc.c("para.keepNext")
    doc.c("para.shading", {"color": LIGHT})
    doc.c("para.borders", {"kind": "left", "width": 3, "color": TEAL})
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": "Portal today: "})
    doc.c("format.resetChar")
    doc.runs(text)
    doc.c("text.newParagraph")
    doc.c("para.shading", {"color": None})
    doc.c("para.borders", {"kind": "none"})


def tick(doc, text, keep_next=True):
    doc.start("Normal")
    if keep_next:
        doc.c("para.keepNext")
    doc.c("para.indents", {"left": 30, "firstLine": -18})
    doc.c("para.set", {"props": {"spaceAfter": 4}})
    doc.c("format.set", {"props": {"size": 13}})
    doc.c("text.insert", {"text": BOX})
    doc.c("format.resetChar")
    doc.c("text.insert", {"text": "  "})
    doc.runs(text)
    doc.c("text.newParagraph")


def write_line(doc, text, keep_next=True, indent=0):
    """A label followed by an underscore leader to the right margin, to write on."""
    doc.start("Normal")
    if keep_next:
        doc.c("para.keepNext")
    if indent:
        doc.c("para.indents", {"left": indent})
    doc.c("para.tabs", {"tabs": [{"pos": TEXT_WIDTH, "align": "right", "leader": "underscore"}]})
    doc.c("para.set", {"props": {"spaceBefore": 8, "spaceAfter": 2}})
    doc.c("text.insert", {"text": text})
    doc.c("text.tab")
    doc.c("text.newParagraph")


def signed_by(doc):
    """'Answered by' and 'Date' lines side by side, each with its own underscore leader."""
    doc.start("Normal")
    doc.c(
        "para.tabs",
        {
            "tabs": [
                {"pos": 235, "align": "left", "leader": "underscore"},
                {"pos": TEXT_WIDTH, "align": "right", "leader": "underscore"},
            ]
        },
    )
    doc.c("para.set", {"props": {"spaceBefore": 8, "spaceAfter": 2}})
    doc.c("text.insert", {"text": "Answered by: "})
    doc.c("text.tab")
    doc.c("text.insert", {"text": "  Date (YYYY-MM-DD): "})
    doc.c("text.tab")
    doc.c("text.newParagraph")


def question(doc, q):
    doc.h2(q["title"])
    label(doc, "Means", q.get("means", ""))
    today(doc, q.get("today", ""))
    if q.get("ask"):
        label(doc, "Ask", q["ask"])
    options = choices(q.get("choices", ""))
    doc.start("Normal")
    doc.c("para.keepNext")
    doc.c("para.set", {"props": {"spaceBefore": 4, "spaceAfter": 3}})
    doc.c("format.set", {"props": {"bold": True, "color": NAVY}})
    doc.c("text.insert", {"text": "Decision (tick one):" if options else "Answer:"})
    doc.c("format.resetChar")
    doc.c("text.newParagraph")
    for option in options:
        tick(doc, option)
    # Skip the extra box when a choice already means keeping today's behaviour
    if options and not any(re.match(r"\([a-z]\) keep\b", o, re.I) for o in options):
        tick(doc, "Keep what the portal does today")
    write_line(doc, "Other or notes: " if options else "", indent=12 if options else 0)
    for _ in range(1 if options else 3):
        write_line(doc, "", indent=12 if options else 0)
    signed_by(doc)
    if q.get("unblocks"):
        doc.start("Normal")
        doc.c("format.set", {"props": {"size": 9, "color": MUTED}})
        doc.c("text.insert", {"text": f"Unblocks: {q['unblocks']}"})
        doc.c("format.resetChar")
        doc.c("text.newParagraph")


def build():
    parts = parse(SOURCE)
    doc = Doc()
    doc.title(
        "Portal Decisions", "Questions for DBGI sales, pricing, and IT. Printable answer sheet."
    )
    doc.para(
        "These answers decide what is built next in the DBGI Project Registration Portal, so it follows how "
        "DBGI actually works. Each question explains what it means and what the portal does today."
    )
    doc.bullets(
        [
            "Tick one choice, tick **Keep what the portal does today**, or write your own rule under **Other**.",
            "The first choice is only a suggested starting point, not a decision.",
            "Write who answered and the date (YYYY-MM-DD) under each question.",
            "Start with **Part A**. If an answer there is a surprise, say so before continuing.",
            "The same questions, with the same ids, are at the end of the **Using the DBGI Portal** slides. "
            "Its walkthrough slides show the screens they refer to.",
            "Skip anything outside your area, and return the sheet to the person who sent it.",
        ]
    )
    write_line(doc, "Meeting date (YYYY-MM-DD): ", keep_next=False)
    write_line(doc, "Attendees: ", keep_next=False)
    write_line(doc, "", keep_next=False)
    for i, part in enumerate(parts):
        doc.h1(part["title"], page_break=True)
        if part["intro"].strip():
            doc.para(part["intro"].strip())
        for q in part["questions"]:
            question(doc, q)
    count = sum(len(p["questions"]) for p in parts)
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = doc.save(OUT)
    pdf = os.path.splitext(OUT)[0] + ".pdf"
    subprocess.run([WC, "convert", OUT, pdf], check=True, capture_output=True)
    preview = os.path.join(HERE, "decision-pages")
    os.makedirs(preview, exist_ok=True)
    for p in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"page-{p:02d}.png"), page=p, scale=1.0)
    print(f"{count} questions, {pages} pages -> {OUT} and {pdf}")


if __name__ == "__main__":
    build()
