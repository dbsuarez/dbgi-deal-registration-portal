"""Crop the 2026-11 guide's raw screenshots (shots2) into crops2; clipped sections and dialogs are copied as they are."""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pylib"))
from PIL import Image  # noqa: E402

SRC = os.path.join(HERE, "shots2")
OUT = os.path.join(HERE, "crops2")
os.makedirs(OUT, exist_ok=True)

MAIN = (130, 90, 1310)  # left, top, right of the page content

# name: (source, (left, top, right, bottom)) in source pixels
CROPS = {
    "login": ("login", (255, 120, 720, 550)),
    "list": ("list", (0, 0, 1440, 640)),
    "help": ("help", (*MAIN, 900)),
    "form-top": ("form-full", (130, 225, 1310, 590)),
    "form-items": ("form-full", (130, 605, 1310, 1070)),
    "form-attachment": ("form-full", (130, 1085, 1310, 1600)),
    "submitted-top": ("submitted-full", (*MAIN, 215)),
    "notifications": ("notifications", (*MAIN, 900)),
    "dashboard": ("dashboard", (285, 60, 1440, 800)),
    "dbgi-list": ("dbgi-list", (0, 0, 1440, 730)),
    "returned-top": ("returned-full", (*MAIN, 215)),
    "edit-top": ("edit-full", (*MAIN, 310)),
    "edit-save": ("edit-full", (130, 1195, 1310, 1700)),
    "confirmed-top": ("confirmed-full", (*MAIN, 215)),
    "price-list": ("price-list", (0, 40, 1440, 460)),
    "price-form": ("price-form", (285, 60, 1440, 560)),
    "price-items": ("price-form", (285, 880, 1440, 1200)),
    "approved-top": ("approved-full", (*MAIN, 265)),
    "rank-partner": ("rank-partner", (0, 90, 1440, 500)),
    "withdrawn-top": ("withdrawn-full", (*MAIN, 215)),
    "project-status": ("project-status", (285, 40, 1440, 625)),
    "price-add": ("price-add", (285, 40, 1440, 760)),
    "rank-dbgi": ("rank-dbgi", (0, 90, 1440, 420)),
}
COPIES = (
    "competitor product sub-next sub-products sub-approvals sub-activity review-card options-card changes-card "
    "ret-next ret-activity confirm-card app-approvals app-products ren-approvals after-approvals out-partner "
    "out-dbgi renewal-request renewal-decide withdraw outcome catalog reprice tie "
    "repeat-request repeat-decide repeat-section merge-dialog split-dialog"
).split()

for name, (source, box) in CROPS.items():
    Image.open(os.path.join(SRC, f"{source}.png")).crop(box).save(os.path.join(OUT, f"{name}.png"))
for name in COPIES:
    shutil.copy(os.path.join(SRC, f"{name}.png"), os.path.join(OUT, f"{name}.png"))
print(len(CROPS) + len(COPIES), "crops")
