"""Build "Portal Decisions - Follow-up" (.docx and .pdf): the questions where the three answer forms differ,
written in plain words for the head of pricing and business development to settle.

Uses roles, not names. Reuses the tick-box and writing-line helpers from build_decisions_doc.py.
"""

import os
import subprocess

from build_decisions_doc import OUT_DIR, label, signed_by, tick, write_line
from doclib import WC, Doc, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "Portal Decisions - Follow-up.docx")

YOU = "Your answer"
BD = "Business development consultant"
PS = "Product specialist (does most Canon and Epson registrations)"

GROUPS = [
    (
        "1. The other two agree with each other, but not with you",
        "For these three questions, the other two people gave the same answer, and it is different from yours.",
        [
            {
                "q": "When should the portal go live?",
                "means": "Whether we start using the portal before price history is ready. Price history means "
                "keeping every old price with its dates, so we always know which price applied when.",
                "answers": [
                    (YOU, "Wait until price history is ready too."),
                    (
                        f"{BD} and {PS.split(' (')[0].lower()}",
                        "Go live once registration, review, and withdrawal work.",
                    ),
                ],
                "choices": [
                    "Keep my answer: wait for price history",
                    "Go live without waiting for price history",
                ],
            },
            {
                "q": "What if two partners register the same deal at exactly the same moment?",
                "means": "Who gets first place when both registrations arrive at the same time. This is very rare: "
                "the portal records the time down to a fraction of a second.",
                "answers": [
                    (YOU, "They share the same rank, and DBGI decides."),
                    (
                        f"{BD} and {PS.split(' (')[0].lower()}",
                        "The registration with better documents wins.",
                    ),
                ],
                "choices": [
                    "Keep my answer: same rank, DBGI decides",
                    "The registration with better documents wins",
                ],
            },
            {
                "q": "How do we count working days?",
                "means": 'Only for deadlines written as working days, for example "reply within one working day". '
                "Periods like 30, 60, or 90 days are always counted as calendar days.",
                "answers": [
                    (YOU, "Monday to Friday, without Philippine holidays, with a 5:00 PM cutoff."),
                    (f"{BD} and {PS.split(' (')[0].lower()}", "Just count calendar days."),
                ],
                "choices": [
                    "Keep my answer: Monday to Friday, no holidays, 5:00 PM cutoff",
                    "Count calendar days",
                ],
            },
        ],
    ),
    (
        "2. All three answers are different",
        "Each person gave a different answer to these two questions.",
        [
            {
                "q": "Can partners change a deal after they submit it?",
                "means": "Today a partner can edit any time. If DBGI already confirmed the deal, DBGI checks it again, "
                "and the deal keeps its place in line.",
                "answers": [
                    (YOU, "Small fixes any time; big changes go back to DBGI for checking."),
                    (BD, "Keep how it works today."),
                    (PS, "Only when DBGI asks for changes."),
                ],
                "choices": [
                    "Keep my answer: small fixes any time, big changes checked again",
                    "Keep how it works today",
                    "Only when DBGI asks for changes",
                ],
                "after": "If you keep your answer, please confirm what counts as small. Suggestion: contact details "
                "and descriptions are small; the end-user, products, quantities, and prices are big.",
            },
            {
                "q": "How long is an approved special price good for?",
                "means": "The number of days a price DBGI approved stays valid, and when the partner gets a reminder "
                "before it ends. Partners can still ask to renew it for 30 more days.",
                "answers": [
                    (YOU, "90 days, reminder 14 days before it ends."),
                    (BD, "60 days, reminder 7 days before."),
                    (PS, "45 days."),
                ],
                "choices": [
                    "Keep my answer: 90 days, reminder 14 days before",
                    "60 days, reminder 7 days before",
                    "45 days, reminder 7 days before",
                ],
            },
        ],
    ),
    (
        "3. Already built: please confirm the number of days",
        "These two rules already work in the portal, using your answers. The product specialist suggested "
        "something different, so please confirm or change them.",
        [
            {
                "q": "How long can a deal wait for DBGI to confirm it?",
                "means": "Built today: after 53 days the partner gets a reminder; after 60 days the deal goes back to "
                "DBGI for review. It is never rejected automatically.",
                "answers": [
                    (YOU, "60 days, reminder 7 days before, then DBGI reviews."),
                    (BD, "Same as yours."),
                    (PS, "3 months would be better."),
                ],
                "choices": ["Keep 60 days", "Change to 90 days (3 months)"],
            },
            {
                "q": "What happens when a tender is postponed or posted again?",
                "means": "Built today: when DBGI puts a project on hold, the partners keep their place in line for "
                "60 days, get a reminder, and then DBGI reviews the deals.",
                "answers": [
                    (YOU, "Same rule as the question above: 60 days, then DBGI reviews."),
                    (BD, "A reposted tender starts a new race."),
                    (
                        PS,
                        "A reposted tender keeps the original place in line (no time limit mentioned).",
                    ),
                ],
                "choices": [
                    "Keep my answer: keep the place for 60 days, then DBGI reviews",
                    "Keep the place with no time limit",
                    "A reposted tender starts a new race",
                ],
            },
        ],
    ),
    (
        "4. New ideas from the product specialist",
        "The product specialist suggested these. Please say yes or no.",
        [
            {
                "q": "Repeat orders: how does a partner ask for the same special price again?",
                "means": "A repeat order is when the same government buyer buys more of the same item from the same "
                "supplier without a new bidding.",
                "answers": [
                    (
                        YOU,
                        "Same end-user, and the NOA and NTP must say it is a repeat order. Otherwise DBGI declines.",
                    ),
                    (
                        PS,
                        'The partner first registers it in the portal, marks it "Repeat order", and enters the code '
                        "of the original approved registration. The proof is the end-user's purchase order.",
                    ),
                ],
                "choices": [
                    "Keep my rule only",
                    "My rule, plus his step: register it in the portal with the original registration code",
                    "His rule: the end-user's purchase order is enough proof",
                ],
            },
            {
                "q": "Should DBGI reviewers also get emails?",
                "means": "Already decided: emails go only to the partner who submitted the deal. DBGI staff see "
                "their tasks inside the portal.",
                "answers": [(PS, "Also email DBGI reviewers when something needs their action.")],
                "choices": ["Yes, email DBGI reviewers too", "No, the portal is enough for DBGI"],
            },
            {
                "q": 'Should "Evidence" be called "Attachment"?',
                "means": "The section where partners upload files and describe their proof of the deal.",
                "answers": [(PS, 'Use "Attachment" instead of "Evidence".')],
                "choices": ['Yes, call it "Attachment"', 'No, keep "Evidence"'],
            },
            {
                "q": 'Is the status name "Changes requested" clear?',
                "means": "The status a partner sees when DBGI sends the deal back for corrections.",
                "answers": [
                    (BD, "It is confusing."),
                    (PS, "The status names are clear."),
                ],
                "choices": [
                    'Keep "Changes requested"',
                    'Rename it to "Needs your update"',
                    'Rename it to "Returned for changes"',
                ],
            },
            {
                "q": "Who sets the backup and recovery targets?",
                "means": "How long records are kept, how often backups run, and how fast the portal must be back "
                "after a problem.",
                "answers": [
                    (YOU, "Keep records 5 years, back up daily, be back within one working day."),
                    (PS, "Let IT set the targets."),
                ],
                "choices": ["Keep my answer", "Let IT set the targets"],
            },
        ],
    ),
]


def question(doc, number, item):
    doc.h2(f"{number}. {item['q']}")
    label(doc, "What it means", item["means"])
    for who, answer in item["answers"]:
        doc.start("Normal")
        doc.c("para.keepNext")
        doc.c("para.indents", {"left": 12})
        doc.c("para.set", {"props": {"spaceAfter": 2}})
        doc.runs(f"**{who}:** {answer}")
        doc.c("text.newParagraph")
    doc.start("Normal")
    doc.c("para.keepNext")
    doc.c("para.set", {"props": {"spaceBefore": 6, "spaceAfter": 3}})
    doc.runs("**Your final decision (tick one):**")
    doc.c("text.newParagraph")
    for choice in item["choices"]:
        tick(doc, choice)
    tick(doc, "Something else (write below)")
    if item.get("after"):
        label(doc, "Note", item["after"])
    write_line(doc, "Notes: ", indent=12)
    write_line(doc, "", indent=12, keep_next=False)


def build():
    doc = Doc()
    doc.title("Portal Decisions: Follow-up", "A few answers to settle before we continue building")
    doc.para(
        "Three people filled in the portal question form: you, a business development consultant, and a product "
        "specialist who does most of the Canon and Epson deal registrations. Your answers were used as the decisions."
    )
    doc.para(
        "On the questions below, the other two answered differently. Their day-to-day experience matters, so "
        "please read their answers and make the final call. Tick one choice for each question, or write your own."
    )
    doc.para(
        "Everything not listed here stays as you decided. Most of your answers matched at least one other person."
    )
    number = 1
    for title, intro, items in GROUPS:
        doc.h1(title)
        doc.para(intro)
        for item in items:
            question(doc, number, item)
            number += 1
    doc.h1("When you are done")
    doc.para(
        "Return this to the person who sent it. Your decisions will update the portal plan and its rules."
    )
    signed_by(doc)
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = doc.save(OUT)
    pdf = os.path.splitext(OUT)[0] + ".pdf"
    subprocess.run([WC, "convert", OUT, pdf], check=True, capture_output=True)
    preview = os.path.join(HERE, "decision-pages")
    os.makedirs(preview, exist_ok=True)
    for p in range(1, pages + 1):
        render(OUT, os.path.join(preview, f"followup-{p:02d}.png"), page=p, scale=0.8)
    print(f"{number - 1} questions, {pages} pages -> {OUT}")
    return pages


if __name__ == "__main__":
    build()
