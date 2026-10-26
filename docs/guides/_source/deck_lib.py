"""Tiny helper for driving deckcraft-cli: build command lists, run them in batches."""

import json
import subprocess

DECK = r"C:\Program Files\DeckCraft\deckcraft-cli.exe"

# Palette (Harbor-like, calm teal and navy)
NAVY = "#12384D"
TEAL = "#1B7FA6"
MINT = "#36B3A8"
SAND = "#F2C14E"
CORAL = "#F78154"
INK = "#1E2B3C"
MUTED = "#5B6B7A"
LIGHT = "#E4EEF2"
WHITE = "#FFFFFF"
RED = "#D64545"
GREEN = "#2EA36F"


def c(cmd, params=None):
    if params is None:
        return cmd
    return f"{cmd}={json.dumps(params)}"


class Slide:
    def __init__(self):
        self.cmds = []

    def add(self, cmd, params=None):
        self.cmds.append(c(cmd, params))
        return self

    def box(
        self,
        rect,
        text="",
        fill=None,
        line=None,
        preset="roundRect",
        size=16,
        color=INK,
        bold=False,
        align="center",
        anchor="middle",
        line_width=1.5,
        font=None,
    ):
        self.add("shape.insert", {"preset": preset, "rect": rect, "text": text})
        if fill:
            self.add("shape.fill", {"color": fill})
        else:
            self.add("shape.fill", {"none": True})
        if line:
            self.add("shape.line", {"color": line, "width": line_width})
        else:
            self.add("shape.line", {"none": True})
        if text:
            self.add(
                "format.fontDialog",
                {"size": size, "bold": bold, "color": color, **({"family": font} if font else {})},
            )
            self.add("format.align", {"align": align})
            self.add("format.anchor", {"anchor": anchor})
            self.add("format.autofit", {"mode": "none"})
            self.add("format.wrap", {"on": True})
        return self

    def text(
        self, rect, text, size=16, color=INK, bold=False, align="left", anchor="top", font=None
    ):
        return self.box(
            rect,
            text,
            preset="rect",
            size=size,
            color=color,
            bold=bold,
            align=align,
            anchor=anchor,
            font=font,
        )

    def arrow(self, x1, y1, x2, y2, color=MUTED, width=2.5):
        x, y = min(x1, x2), min(y1, y2)
        w, h = max(abs(x2 - x1), 1), max(abs(y2 - y1), 1)
        self.add("shape.insert", {"preset": "straightConnector1", "rect": [x, y, w, h]})
        self.add(
            "shape.line", {"color": color, "width": width, "tail": "triangle", "tailSize": "med"}
        )
        if x2 < x1:
            self.add("shape.flip", {"axis": "horizontal"})
        if y2 < y1:
            self.add("shape.flip", {"axis": "vertical"})
        return self

    def icon(self, name, rect, color):
        self.add("insert.icon", {"name": name, "rect": rect})
        self.add("shape.line", {"color": color})
        return self

    def header(self, title, subtitle=None):
        self.box([60, 30, 56, 6], fill=TEAL, preset="rect")
        self.text([56, 42, 850, 50], title, size=28, bold=True, color=NAVY)
        if subtitle:
            self.text([58, 92, 850, 30], subtitle, size=15, color=MUTED)
        return self

    def note(self, rect, text, fill=LIGHT, color=NAVY, size=14, icon=None):
        self.box(rect, text, fill=fill, size=size, color=color, align="left", preset="roundRect")
        self.add("format.margins", {"left": 44 if icon else 14, "right": 14})
        if icon:
            self.icon(icon, [rect[0] + 12, rect[1] + rect[3] / 2 - 11, 22, 22], color)
        return self


def run(cmds, src=None, save=None, export=None, export_params=None):
    args = [DECK, "run"]
    if src:
        args += ["--in", src]
    for x in cmds:
        args += ["--cmd", x]
    if save:
        args += ["--save", save]
    if export:
        args += ["--export", export]
    if export_params:
        args += ["--export-params", json.dumps(export_params)]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"deckcraft failed:\n{r.stderr}\n{r.stdout[-2000:]}")
    return r.stdout
