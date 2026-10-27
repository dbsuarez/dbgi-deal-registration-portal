# DeckCraft and WordCraft CLI notes for AI agents

Read this instead of running `--help`, `commands`, or `describe`; everything below was verified on 2026-10-26.
Start from the working scripts in this folder (`deck_lib.py`, `build_*.py`) rather than writing new ones.

## Shared rules

- Drive both CLIs from Python with `subprocess.run([exe, ...args])`. Passing JSON through PowerShell or `--cmd` quoting breaks.
- Never convert Markdown to `.docx`; the user rejected the formatting. Build Word files with WordCraft commands.
- Always render the output to PNG and look at it before reporting done.
- Pillow lives in `pylib/` (`python -m pip install --target pylib pillow`); scripts add it to `sys.path`.

## WordCraft (`C:\Program Files\WordCraft\wordcraft-cli.exe`)

Run a script: `wordcraft-cli run --script script.json`, where the file is
`{"commands": [{"command": "id", "params": {...}}, ...], "save": ["out.docx"]}`.
The JSON must be UTF-8 **without BOM** (PowerShell `Set-Content -Encoding utf8` adds one and fails with "bad JSON").

Check output: `wordcraft-cli info out.docx` (JSON with `pages`), `wordcraft-cli render out.docx p.png --page N --scale 1.2` (pages start at 1).

| Purpose | Command and params |
| --- | --- |
| Page setup | `layout.size {"name": "A4"}`, `layout.margins {"preset": "normal"}` (A4 text width is 451 pt) |
| Style defaults | `styles.modify {"style": "Heading1", "chr": {"font", "size", "bold", "color": "RRGGBB"}, "para": {"spaceBefore", "spaceAfter"}}` (a float `lineSpacing` is rejected) |
| Paragraph style | `para.style {"style": "Normal" \| "Heading1" \| "Heading2" \| "Caption"}` |
| Text | `text.insert {"text"}`, `text.newParagraph`, `text.pageBreak` |
| Inline bold or color | `format.set {"props": {"bold": true, "size", "color"}}` then `format.resetChar` (setting props to null does not reset) |
| Lists | `para.bullets` / `para.bullets {"off": true}`; `para.numbering {"kind": "numbered"}` + `para.restartNumbering` / `{"off": true}` |
| Callout | `para.shading {"color": "E4EEF2"}`, `para.borders {"kind": "left", "width": 3, "color"}`; clear with `{"color": null}` and `{"kind": "none"}` |
| Keep with next | `para.keepNext`; spacing `para.set {"props": {"spaceBefore": 10}}`; align `para.alignCenter` / `para.alignLeft` |
| Picture | `insert.picture {"path", "width": pt, "alt"}` |
| Table | `insert.table {"rows", "cols", "style": "GridTable4AccentBlue"}` (also TableGrid, ListTable3AccentBlue, Green/Orange/Purple variants), `table.autofit {"mode": "fixed"}`; caret starts in cell (0,0), `text.tab` moves to the next cell, `caret.docEnd` leaves the table |
| Column width | `table.columnWidth {"width": pt}` acts on the caret's column, so set it while in each header cell |
| Page numbers | `insert.pageNumber {"position": "bottom", "align": "center"}` (do this last) |

Gotcha: `para.set` and `format.set` carry over into every following paragraph. Start each block with
`para.style`, `para.reset`, `format.resetChar` (see `start()` in `build_portal_doc.py`).

## DeckCraft (`C:\Program Files\DeckCraft\deckcraft-cli.exe`)

`deckcraft-cli run [--in deck.deckcraft] --cmd 'id={json}' ... --save deck.deckcraft [--export out.png --export-params '{"slide": i}']`.
There is no script file option, and Windows limits command-line length, so build **one slide per run**
(`--in` and `--save` the same file). `deck_lib.run()` does this.

- Slide is 960 x 540 pt; every `rect` is `[x, y, w, h]`.
- First slide: `design.theme {"name": "Harbor"}`, `slide.layout {"layout": "blank"}`. Later slides: `slide.last`, then `slide.new {"layout": "blank"}`.
- Inserting a shape selects it; the next `shape.*` and `format.*` commands act on that selection.

| Purpose | Command and params |
| --- | --- |
| Shape | `shape.insert {"preset": "rect" \| "roundRect" \| "ellipse" \| "straightConnector1", "rect", "text"}` |
| Fill and outline | `shape.fill {"color": "#RRGGBB"}` or `{"none": true}`; `shape.line {"color", "width", "tail": "triangle"}` or `{"none": true}` |
| Arrow direction | connectors draw left-to-right and top-to-bottom; use `shape.flip {"axis": "horizontal" \| "vertical"}` |
| Text style | `format.fontDialog {"size", "bold", "color", "family"}`, `format.align {"align"}`, `format.anchor {"anchor": "middle"}`, `format.autofit {"mode": "none"}`, `format.wrap {"on": true}`, `format.margins {"left", ...}` |
| Numbered text | `format.numbering {"on": true, "scheme": "arabicPeriod", "color"}`, `format.paragraph {"spaceAfter"}` |
| Icon | `insert.icon {"name", "rect"}` then `shape.line {"color"}` (icons are outlines; fill does nothing) |
| Picture | `insert.picture {"path", "rect"}`; compute the rect to keep the aspect ratio (`pic()` in `build_portal_deck.py`) |
| Table | `insert.table {"rows", "cols", "rect"}`, `table.style {"style": "medium2-accent1"}`, `text.set {"text", "cell": [r, c]}`, then `text.exit`, `format.size`, `table.cellAlign {"anchor": "middle"}`, `table.columnWidth {"col", "width"}` |
| Slide background | `design.background {"color"}` (current slide) |
| Slide numbers | `design.headerFooter {"slideNumber": true, "hideOnTitle": true, "all": true}` |
| Title metadata | `file.properties {"title"}` (a rebuild clears it, so set it again) |

Icon names: arrow-up/down/left/right, chevron-right, undo-2, refresh-cw, check, x, plus, minus, star, flag, award,
circle-check, triangle-alert, user, users, circle-user, calendar, clock, hourglass, mail, phone, message-circle,
bell, megaphone, chart-column, chart-bar, chart-pie, trending-up, target, lightbulb, file, file-text, folder,
clipboard, link, house, map-pin, globe, building, briefcase, image, search, info, circle-alert, lock, key, settings.

Export one slide: `run --in deck --cmd 'slide.go={"index": i}' --export s.png --export-params '{"slide": i}'`.
PowerPoint copy: `deckcraft-cli convert deck.deckcraft deck.pptx`. Slide list: `deckcraft-cli info deck`.
