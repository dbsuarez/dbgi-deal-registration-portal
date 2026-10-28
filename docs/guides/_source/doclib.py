"""Small helper for building Word documents with wordcraft-cli commands.

Collect commands with a `Doc`, then `save()` writes the script JSON (UTF-8, no BOM) and runs it.
Every block starts with `start()`, which drops direct formatting carried over from the previous paragraph.
"""

import json
import os
import re
import subprocess

WC = r"C:\Program Files\WordCraft\wordcraft-cli.exe"

NAVY, TEAL, MUTED, LIGHT = "12384D", "1B7FA6", "5B6B7A", "E4EEF2"
WARN, WARN_EDGE = "FDF1D6", "E3B21C"
GOOD, GOOD_EDGE = "E3F4EC", "2EA36F"

TEXT_WIDTH = 451  # A4 with normal margins, in points


class Doc:
    def __init__(self, font="Calibri"):
        self.cmds = []
        self.after_table = False
        self.figure_no = 0
        self.c("layout.size", {"name": "A4"})
        self.c("layout.margins", {"preset": "normal"})
        self.c(
            "styles.modify",
            {"style": "Normal", "chr": {"font": font, "size": 11}, "para": {"spaceAfter": 6}},
        )
        self.c(
            "styles.modify",
            {
                "style": "Heading1",
                "chr": {"font": font, "size": 18, "bold": True, "color": NAVY},
                "para": {"spaceBefore": 18, "spaceAfter": 8},
            },
        )
        self.c(
            "styles.modify",
            {
                "style": "Heading2",
                "chr": {"font": font, "size": 14, "bold": True, "color": TEAL},
                "para": {"spaceBefore": 12, "spaceAfter": 4},
            },
        )

    def c(self, command, params=None):
        self.cmds.append(
            {"command": command, "params": params} if params is not None else {"command": command}
        )

    def runs(self, text):
        """Type text, turning **x** into bold runs."""
        for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
            if not part:
                continue
            if i % 2:
                self.c("format.set", {"props": {"bold": True}})
                self.c("text.insert", {"text": part})
                self.c("format.resetChar")
            else:
                self.c("text.insert", {"text": part})

    def start(self, style):
        """Begin a block in `style`, dropping direct formatting carried over from the previous paragraph."""
        self.c("para.style", {"style": style})
        self.c("para.reset")
        self.c("format.resetChar")
        if self.after_table:
            self.c("para.set", {"props": {"spaceBefore": 10}})
            self.after_table = False

    def title(self, text, subtitle=None):
        self.start("Normal")
        self.c("para.set", {"props": {"spaceBefore": 110, "spaceAfter": 4}})
        self.c("format.set", {"props": {"bold": True, "size": 30, "color": NAVY}})
        self.c("text.insert", {"text": text})
        self.c("format.resetChar")
        self.c("text.newParagraph")
        if subtitle:
            self.start("Normal")
            self.c("format.set", {"props": {"size": 14, "color": MUTED}})
            self.c("text.insert", {"text": subtitle})
            self.c("format.resetChar")
            self.c("text.newParagraph")

    def para(self, text):
        self.start("Normal")
        self.runs(text)
        self.c("text.newParagraph")

    def h1(self, text, page_break=False):
        if page_break:
            self.c("text.pageBreak")
        self.start("Heading1")
        self.c("para.keepNext")
        self.c("text.insert", {"text": text})
        self.c("text.newParagraph")

    def h2(self, text):
        self.start("Heading2")
        self.c("para.keepNext")
        self.c("text.insert", {"text": text})
        self.c("text.newParagraph")

    def bullets(self, items, numbered=False):
        self.start("Normal")
        if numbered:
            self.c("para.numbering", {"kind": "numbered"})
            self.c("para.restartNumbering")
        else:
            self.c("para.bullets")
        for item in items:
            self.runs(item)
            self.c("text.newParagraph")
        self.c("para.numbering" if numbered else "para.bullets", {"off": True})

    def callout(self, text, color=LIGHT, edge=TEAL):
        self.start("Normal")
        self.c("para.shading", {"color": color})
        self.c("para.borders", {"kind": "left", "width": 3, "color": edge})
        self.runs(text)
        self.c("text.newParagraph")
        self.c("para.shading", {"color": None})
        self.c("para.borders", {"kind": "none"})

    def warn(self, text):
        self.callout(text, color=WARN, edge=WARN_EDGE)

    def good(self, text):
        self.callout(text, color=GOOD, edge=GOOD_EDGE)

    def picture(self, path, caption, width=TEXT_WIDTH):
        self.figure_no += 1
        self.start("Normal")
        self.c("para.keepNext")
        self.c("para.alignCenter")
        self.c("insert.picture", {"path": os.path.abspath(path), "width": width, "alt": caption})
        self.c("text.newParagraph")
        self.start("Caption")
        self.c("para.alignCenter")
        self.c("text.insert", {"text": f"Figure {self.figure_no}. {caption}"})
        self.c("text.newParagraph")
        self.start("Normal")

    def table(self, rows, widths, style="GridTable4AccentBlue"):
        """A table; `widths` are column widths in points (sum to TEXT_WIDTH for full width)."""
        self.start("Normal")
        self.c("insert.table", {"rows": len(rows), "cols": len(rows[0]), "style": style})
        self.c("table.autofit", {"mode": "fixed"})
        first = True
        for r, row in enumerate(rows):
            for col, cell in enumerate(row):
                if not first:
                    self.c("text.tab")
                first = False
                if r == 0:
                    # columnWidth acts on the caret's column, so size each column from its header cell
                    self.c("table.columnWidth", {"width": widths[col]})
                self.runs(cell)
        self.c("caret.docEnd")
        self.after_table = True

    def save(self, out, page_numbers=True, keep_script=False):
        """Write the script, run it, and return the page count."""
        if page_numbers:
            self.c("insert.pageNumber", {"position": "bottom", "align": "center"})
        out = os.path.abspath(out)
        script = os.path.splitext(out)[0] + "-script.json"
        with open(script, "w", encoding="utf-8") as f:  # plain utf-8 writes no BOM
            json.dump({"commands": self.cmds, "save": [out]}, f, ensure_ascii=False, indent=1)
        r = subprocess.run(
            [WC, "run", "--script", script], capture_output=True, text=True, encoding="utf-8"
        )
        if not keep_script:
            os.remove(script)
        if r.returncode != 0:
            raise SystemExit(f"wordcraft failed:\n{r.stderr[-2000:]}\n{r.stdout[-1000:]}")
        info = subprocess.run([WC, "info", out], capture_output=True, text=True, encoding="utf-8")
        return json.loads(info.stdout)["pages"]


def render(docx, png, page=1, scale=1.2):
    """Render one page (pages start at 1) to PNG so you can look at it."""
    subprocess.run(
        [WC, "render", docx, png, "--page", str(page), "--scale", str(scale)], check=True
    )
