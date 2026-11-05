"""Build the 2026-11 portal guide (deck and Word) from guide2_content.py into one folder.

Usage: python build_guide2.py [deck] [doc]. Takes no question slides; those stay in the older guide.
"""

import os
import sys

import deck_lib
import doclib
from deck_lib import GREEN, INK, LIGHT, MUTED, NAVY, SAND, TEAL, WHITE, Slide, c, run
from guide2_content import PAGES, PARTS, SAMPLE_NOTE, SUBTITLE, TITLE

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pylib"))
from PIL import Image  # noqa: E402

CROPS = os.path.join(HERE, "crops2")
FOLDER = os.path.normpath(os.path.join(HERE, "..", "Portal User Guide 2026-11"))
os.makedirs(FOLDER, exist_ok=True)
DECK_OUT = os.path.join(FOLDER, f"{TITLE}.deckcraft")
PPTX_OUT = os.path.join(FOLDER, f"{TITLE}.pptx")
DOC_OUT = os.path.join(FOLDER, f"{TITLE}.docx")
PNG_DIR = os.path.join(HERE, "portal-slides", "guide2")

BORDER = "#C9D6DE"
WARN_FILL, WARN_INK = "#FDF1D6", "#8A5A00"
ROLE = {
    "partner": ("Partner", TEAL),
    "dbgi": ("DBGI", NAVY),
    "both": ("Everyone", GREEN),
    None: ("", MUTED),
}


def plain(text):
    return text.replace("**", "")


def size_of(name):
    return Image.open(os.path.join(CROPS, f"{name}.png")).size


def pic(s, name, box):
    w, h = size_of(name)
    bx, by, bw, bh = box
    scale = min(bw / w, bh / h)
    pw, ph = round(w * scale, 1), round(h * scale, 1)
    s.add(
        "insert.picture",
        {"path": os.path.join(CROPS, f"{name}.png"), "rect": [bx + (bw - pw) / 2, by, pw, ph]},
    )
    s.add("shape.line", {"color": BORDER, "width": 1})
    return ph


def steps_box(s, rect, items, size=14, numbered=True):
    s.box(
        rect,
        "\n".join(plain(i) for i in items),
        preset="rect",
        size=size,
        color=INK,
        align="left",
        anchor="top",
    )
    if numbered:
        s.add("format.numbering", {"on": True, "scheme": "arabicPeriod", "color": TEAL})
    s.add("format.paragraph", {"spaceAfter": 6})
    s.add("format.margins", {"left": 4, "right": 4, "top": 2})


def lines(text, chars):
    return max(1, -(-len(plain(text)) // chars))


def callouts(s, page, rect):
    """Draw the tip or warning at `rect`."""
    if page.get("warn"):
        s.note(
            rect,
            plain(page["warn"]),
            fill=WARN_FILL,
            color=WARN_INK,
            size=13,
            icon="triangle-alert",
        )
    elif page.get("tip"):
        s.note(rect, plain(page["tip"]), size=13, icon="lightbulb")


def callout_h(page, width):
    text = page.get("warn") or page.get("tip")
    if not text:
        return 0
    return 16 + 18 * lines(text, int((width - 60) / 6.3))


def table(s, rows, widths, rect, size):
    s.add("insert.table", {"rows": len(rows), "cols": len(rows[0]), "rect": rect})
    s.add("table.style", {"style": "medium2-accent1"})
    for r, row in enumerate(rows):
        for col, cell in enumerate(row):
            if cell:
                s.add("text.set", {"text": cell, "cell": [r, col]})
    s.add("text.exit")
    s.add("format.size", {"size": size})
    s.add("table.cellAlign", {"anchor": "middle"})
    total = sum(widths)
    for col, share in enumerate(widths):
        s.add("table.columnWidth", {"col": col, "width": rect[2] * share / total})


def header(s, page):
    label, col = ROLE[page["role"]]
    part = page["part"]
    chip = f"Part {part}" + (f"  |  {label}" if label else "") if part else label
    s.box([60, 30, 56, 6], fill=TEAL, preset="rect")
    s.text([56, 42, 640, 48], page["title"], size=26, bold=True, color=NAVY)
    if chip:
        s.box(
            [710, 44, 190, 28], chip, fill=col if part else MUTED, size=12, color=WHITE, bold=True
        )
    y = 94
    if page.get("intro"):
        n = lines(page["intro"], 118)
        s.text([58, y, 842, 22 * n + 6], page["intro"], size=15, color=MUTED)
        y += 22 * n + 8
    return y


def draw_flow(s, flow, y):
    w, h, gap = 262, 100, 28
    for i, (label, role) in enumerate(flow):
        col, row = i % 3, i // 3
        x, top = 60 + col * (w + gap), y + 20 + row * (h + 56)
        fill = TEAL if role == "partner" else NAVY
        s.box([x, top, w, h], f"{i + 1}. {label}", fill=fill, size=15, color=WHITE, bold=True)
        if col < 2 and i < len(flow) - 1:
            s.arrow(x + w + 3, top + h / 2, x + w + gap - 3, top + h / 2)
    s.box([60, 410, 16, 16], fill=TEAL, preset="rect")
    s.text([80, 404, 120, 26], "Partner", size=13, color=MUTED)
    s.box([180, 410, 16, 16], fill=NAVY, preset="rect")
    s.text([200, 404, 120, 26], "DBGI", size=13, color=MUTED)


def draw_page(s, page):
    y = header(s, page)
    pics = page.get("pics", [])
    items = page.get("steps", [])
    bottom = 512
    if page.get("flow"):
        draw_flow(s, page["flow"], y)
        return
    if page.get("bullets"):
        steps_box(s, [60, y + 16, 840, 320], page["bullets"], size=20)
        return
    if page.get("table") and pics:
        # the table on the left, the picture on the right
        rows = page["table"]
        widths = page["widths"]
        table(s, rows, widths, [60, y + 8, 380, 44 * len(rows)], 13)
        pic(s, pics[0][0], [455, y + 8, 445, bottom - y - 8])
        callouts(s, page, [60, y + 24 + 44 * len(rows) + 14, 380, callout_h(page, 380)])
        return
    if page.get("table"):
        rows = page["table"]
        row_h = min(44, (bottom - y - 8 - callout_h(page, 840) - 14) / len(rows))
        size = 14 if row_h >= 34 else 13
        table(s, rows, page["widths"], [60, y + 8, 840, row_h * len(rows)], size)
        ch = callout_h(page, 840)
        if ch:
            callouts(s, page, [60, min(y + 8 + row_h * len(rows) + 30, bottom - ch), 840, ch])
        return
    wide = pics and all(size_of(n)[0] / size_of(n)[1] >= 2.2 for n, _ in pics) and len(pics) == 1
    if not pics:
        ch = callout_h(page, 840)
        steps_box(s, [60, y + 8, 840, bottom - y - ch - 20], items, size=16)
        if ch:
            callouts(s, page, [60, bottom - ch, 840, ch])
    elif wide or not items:
        ch = callout_h(page, 840)
        steps_h = sum(6 + 20 * lines(i, 100) for i in items) + 6 if items else 0
        top = y + 6
        height = bottom - top - steps_h - (ch + 8 if ch else 0) - 6
        ph = pic(s, pics[0][0], [60, top, 840, height])
        cursor = top + ph + 8
        if items:
            steps_box(s, [60, cursor, 840, steps_h], items)
            cursor += steps_h
        if ch:
            callouts(s, page, [60, cursor + 2, 840, ch])
    else:
        col_w = 330
        steps_h = sum(6 + 20 * lines(i, 38) for i in items) + 8
        steps_box(s, [60, y + 6, col_w, steps_h], items)
        ch = callout_h(page, col_w)
        if ch:
            callouts(s, page, [60, min(y + 6 + steps_h + 8, bottom - ch), col_w, ch])
        px, pw = 405, 495
        top = y + 6
        area = bottom - top - 8 * (len(pics) - 1)
        natural = [size_of(n)[1] / size_of(n)[0] * pw for n, _ in pics]
        scale = min(1, area / sum(natural))
        for (name, _), n in zip(pics, natural):
            top += pic(s, name, [px, top, pw, n * scale]) + 8


def build_deck():
    os.makedirs(PNG_DIR, exist_ok=True)
    s = Slide()
    s.add("design.theme", {"name": "Harbor"})
    s.add("slide.layout", {"layout": "blank"})
    s.add("design.background", {"color": NAVY})
    s.box([60, 150, 70, 8], fill=SAND, preset="rect")
    s.text([56, 170, 860, 80], TITLE, size=44, bold=True, color=WHITE)
    s.text([58, 250, 840, 40], SUBTITLE, size=20, color=LIGHT)
    s.text([58, 430, 840, 50], SAMPLE_NOTE, size=13, color=LIGHT)
    run(s.cmds, save=DECK_OUT)

    s = Slide()
    s.add("slide.last")
    s.add("slide.new", {"layout": "blank"})
    s.box([60, 30, 56, 6], fill=TEAL, preset="rect")
    s.text([56, 42, 840, 48], "What this guide covers", size=26, bold=True, color=NAVY)
    numbered = [(n, name) for n, name in PARTS.items() if n]
    for i, (n, name) in enumerate(numbered):
        col, row = i // 8, i % 8
        x, top = 60 + col * 430, 104 + row * 50
        s.box(
            [x, top, 40, 40],
            str(n),
            fill=TEAL if n < 15 else NAVY,
            size=15,
            color=WHITE,
            bold=True,
            preset="ellipse",
        )
        s.add("format.margins", {"left": 0, "right": 0})
        s.add("format.wrap", {"on": False})
        s.text([x + 52, top + 2, 360, 36], name, size=18, color=INK, anchor="middle")
    run(s.cmds, src=DECK_OUT, save=DECK_OUT)

    for i, page in enumerate(PAGES):
        s = Slide()
        s.add("slide.last")
        s.add("slide.new", {"layout": "blank"})
        draw_page(s, page)
        try:
            run(s.cmds, src=DECK_OUT, save=DECK_OUT)
        except SystemExit as exc:
            raise SystemExit(f"page {i} ({page['title']}): {exc}")
    run(
        [
            c("design.headerFooter", {"slideNumber": True, "hideOnTitle": True, "all": True}),
            c("file.properties", {"title": TITLE}),
        ],
        src=DECK_OUT,
        save=DECK_OUT,
    )
    total = len(PAGES) + 2
    for f in os.listdir(PNG_DIR):
        if f.startswith("slide-"):
            os.remove(os.path.join(PNG_DIR, f))
    for i in range(total):
        run(
            [c("slide.go", {"index": i})],
            src=DECK_OUT,
            export=os.path.join(PNG_DIR, f"slide-{i + 1:02d}.png"),
            export_params={"slide": i},
        )
    deck_lib.subprocess.run(
        [deck_lib.DECK, "convert", DECK_OUT, PPTX_OUT], check=True, capture_output=True
    )
    print(f"built {total} slides -> {PPTX_OUT}")


def build_doc():
    os.makedirs(PNG_DIR, exist_ok=True)
    d = doclib.Doc()
    d.title(TITLE, SUBTITLE)
    d.para(SAMPLE_NOTE)
    d.para(
        "**How to use this guide.** Each part says who it is for. Partners can skip the parts marked DBGI."
    )
    d.h2("What is in this guide")
    d.bullets([f"Part {n}: {name}" for n, name in PARTS.items() if n])
    current = None
    for page in PAGES:
        if page["part"] != current:
            current = page["part"]
            name = PARTS[current]
            d.h1(f"Part {current}: {name}" if current else name, page_break=current in (0, 1))
        label = ROLE[page["role"]][0]
        d.h2(f"{page['title']} ({label})" if label and current else page["title"])
        if page.get("intro"):
            d.para(page["intro"])
        if page.get("flow"):
            d.bullets([f"{label} ({ROLE[role][0]})" for label, role in page["flow"]], numbered=True)
        if page.get("steps"):
            d.bullets(page["steps"], numbered=True)
        if page.get("bullets"):
            d.bullets(page["bullets"])
        if page.get("table"):
            total = sum(page["widths"])
            widths = [round(doclib.TEXT_WIDTH * w / total) for w in page["widths"]]
            d.table(page["table"], widths)
        for name, caption in page.get("pics", []):
            w, _ = size_of(name)
            d.picture(
                os.path.join(CROPS, f"{name}.png"),
                caption,
                width=min(doclib.TEXT_WIDTH, w * 0.42 if w < 700 else doclib.TEXT_WIDTH),
            )
        if page.get("warn"):
            d.warn(page["warn"])
        if page.get("tip"):
            d.callout(page["tip"])
    pages = d.save(DOC_OUT)
    print(f"built {pages} pages -> {DOC_OUT}")
    for page in range(1, pages + 1):
        doclib.render(DOC_OUT, os.path.join(PNG_DIR, f"doc-{page:02d}.png"), page=page, scale=0.7)


if __name__ == "__main__":
    what = sys.argv[1:] or ["deck", "doc"]
    for page in PAGES:
        text = str(page)
        assert chr(0x2013) not in text and chr(0x2014) not in text, page["title"]
    if "deck" in what:
        build_deck()
    if "doc" in what:
        build_doc()
