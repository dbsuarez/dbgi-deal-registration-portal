How to rebuild the guides
=========================

Everything here regenerates the files in the two guide folders (docs/guides). Run commands from
this folder. Needs Python, DeckCraft (C:\Program Files\DeckCraft) and WordCraft (C:\Program Files\WordCraft).

Git tracks these sources and the finished guides in the two guide folders. pylib\ and the
intermediate output written here (.docx, .deckcraft, portal-slides\) are ignored (see .gitignore).

CLI_NOTES.md lists the DeckCraft and WordCraft commands and gotchas used by these scripts.

Folders
  shots\    raw portal screenshots (1440 px wide), captured 2026-10-26
  crops\    screenshots cropped for the portal guide (made by crop_shots.py)
  slides\   slide images from the Deal Registration deck, used inside its Word guide
  pylib\    Pillow image library used by the scripts (reinstall with:
            python -m pip install --target pylib pillow)

Deal Registration Guide (general explainer)
  1. python build_deck.py   -> deal-registration.deckcraft and slides\*.png
  2. python build_doc.py    -> Deal Registration Guide.docx (uses slides\*.png)

Portal User Guide (portal walkthrough for colleagues)
  1. python crop_shots.py          -> crops\*.png (only after changing shots\)
  2. python build_portal_deck.py   -> portal-guide.deckcraft and portal-slides\*.png
  3. python build_portal_doc.py    -> Portal User Guide.docx
  The deck ends with one slide per question from docs\DECISIONS_TO_MAKE_2026-10-28.md (read through
  build_decisions_doc.py), so after editing the questions rebuild both the deck and the printable sheet.

Portal Decisions (printable question sheet for DBGI)
  python build_decisions_doc.py   -> Decision Questions\DBGI Portal Decisions.docx and .pdf
  It reads docs\DECISIONS_TO_MAKE_2026-10-28.md, so edit the questions there and rebuild.
  python build_answer_form.py     -> Decision Questions\DBGI Portal Answer Form.docx (fill-in form with drop-downs,
                                     sent with the deck; slide numbers come from build_portal_deck.py)
  Page previews go to decision-pages\ (ignored).

Then copy the new files into the guide folders, and make the PowerPoint copy with:
  "C:\Program Files\DeckCraft\deckcraft-cli.exe" convert <file>.deckcraft <file>.pptx

Updating a screenshot
  Replace the file in shots\ with the same name, adjust its crop box in crop_shots.py
  if the layout moved, then run steps 1 to 3 of the portal guide.

Content source
  Take every rule and workflow from docs\PORTAL_RULES.md. Describe only rules marked Live as
  available; never present a Decided rule as working.

Sample end-user
  At the next refresh, the example deal uses the City of Lucena Mayor's Office, Lucena City Government
  Complex, Diversion Road, Barangay Mayao Kanluran, Lucena City, Quezon 4301, instead of the Pasig City
  Schools Division Office. Update the text in the deck and Word guide, and retake the screenshots.

Rules for the portal guide (it is shared with colleagues)
  - Use plain English anyone can understand: short sentences and everyday words.
  - Use only demo or test accounts in screenshots.
  - Do not show other partner companies' names or data.
  - Do not name the author.

Portal User Guide 2026-11 (slides and Word in one folder, no question slides)
- Words: guide2_content.py, shared by both files. Plain English only.
- Screenshots: reseed the demo database (guide_settings.py, guide_seed.py), then from frontend/ run
  npx playwright test -c playwright.guide.config.ts. Pictures land in shots2.
- Build: python crop_guide2.py, then python build_guide2.py. Check pictures land in portal-slides/guide2.
