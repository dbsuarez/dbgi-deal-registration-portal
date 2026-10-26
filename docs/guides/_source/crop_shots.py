"""Crop the raw portal screenshots into focused images for the deck and the Word guide."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylib"))
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "shots")
OUT = os.path.join(HERE, "crops")
os.makedirs(OUT, exist_ok=True)

# name: (source file, (left, top, right, bottom)) in source pixels; None box = whole image
CROPS = {
    "login": ("01-login.png", None),
    "list": ("02-company-list.png", (0, 0, 1440, 480)),
    "enduser": ("04-enduser-search.png", (130, 80, 1310, 560)),
    "competitor": ("05-competitor-dialog.png", (420, 268, 1020, 632)),
    "product": ("06-product-dialog.png", (410, 280, 1030, 620)),
    "evidence-submit": ("07-form-complete-full.png", (130, 1150, 1310, 1680)),
    "submitted-top": ("08-company-detail-submitted-full.png", (130, 90, 1310, 330)),
    "submitted-pricing": ("08-company-detail-submitted-full.png", (130, 975, 1310, 1480)),
    "notifications": ("09-company-notifications.png", (130, 80, 1310, 740)),
    "help": ("10-help.png", None),
    "dashboard": ("11-admin-dashboard.png", (0, 0, 1440, 790)),
    "start-review": ("12-admin-detail-full.png", (130, 95, 1310, 680)),
    "decision-options": ("14-admin-decision-options.png", None),
    "changes-requested": ("16-company-changes-requested.png", (130, 90, 1310, 330)),
    "activity-reason": ("17-company-activity-reason.png", None),
    "edit-evidence": ("18-company-edit-evidence.png", None),
    "resubmitted": ("19-company-resubmitted.png", (130, 90, 1310, 330)),
    "activity-changes": ("20-admin-activity-changes.png", None),
    "create-opportunity": ("21-admin-create-opportunity.png", None),
    "pricing-top": ("23a-admin-pricing-top.png", (288, 64, 1440, 700)),
    "pricing-items": ("23b-admin-pricing-items.png", (0, 0, 1120, 345)),
    "approved-top": ("26-company-approved-full.png", (130, 100, 1310, 350)),
    "approved-pricing": ("26-company-approved-full.png", (130, 1005, 1310, 1560)),
    "notifications-after": ("25-company-notifications-after.png", (130, 230, 1310, 680)),
    "rankings": ("27-company-rankings.png", (0, 80, 1440, 520)),
}

for name, (src, box) in CROPS.items():
    im = Image.open(os.path.join(SRC, src)).convert("RGB")
    if box:
        im = im.crop(box)
    im.save(os.path.join(OUT, f"{name}.png"))
    print(f"{name}: {im.size[0]}x{im.size[1]}")
