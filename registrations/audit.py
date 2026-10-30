def registration_snapshot(registration):
    return {
        "end_user_name": registration.end_user_name,
        "end_user_address": registration.end_user_address,
        "project_title": registration.project_title,
        "bid_date": registration.bid_date.isoformat(),
        "delivery_date": registration.delivery_date.isoformat(),
        "contact_person": registration.contact_person,
        "contact_designation": registration.contact_designation,
        "contact_email": registration.contact_email,
        "contact_number": registration.contact_number,
        "evidence_description": registration.evidence_description,
        "evidence_url": registration.evidence_url,
        "evidence_sharing_confirmed": registration.evidence_sharing_confirmed,
        "status": registration.status,
        "project_status": registration.project_status,
        "price_status": registration.price_status,
        "version": registration.version,
        "competitor_items": [
            {
                "brand": item.brand,
                "item_name": item.item_name,
                "bid_price": str(item.bid_price),
                "remarks": item.remarks,
            }
            for item in registration.competitor_items.all()
        ],
        "items": [
            {
                "product": item.product.code if item.product_id else None,
                "non_catalog_name": item.non_catalog_name,
                "quantity": item.quantity,
                "requested_unit_price": str(item.requested_unit_price),
                "currency": item.currency,
                "list_unit_price_snapshot": str(item.list_unit_price_snapshot),
                "justification": item.justification,
            }
            for item in registration.items.select_related("product").all()
        ],
        "attachments": [
            {"name": item.original_name, "description": item.description}
            for item in registration.attachments.all()
        ],
    }


CHANGE_LABELS = {
    "end_user_name": "End-user",
    "end_user_address": "End-user address",
    "project_title": "Project title",
    "bid_date": "Bid date",
    "delivery_date": "Delivery date",
    "contact_person": "Contact person",
    "contact_designation": "Contact designation",
    "contact_email": "Contact email",
    "contact_number": "Contact number",
    "evidence_description": "Attachment description",
    "evidence_url": "Attachment link",
    "evidence_sharing_confirmed": "Attachment sharing confirmation",
    "status": "Registration status",
    "project_status": "Project status",
    "price_status": "Commercial status",
    "version": "Version",
}


def registration_change_summary(before, after):
    return [
        f"{change['label']}: {change['previous']} to {change['current']}"
        if change["previous"]
        else f"{change['label']}: {change['current'].lower()}"
        for change in registration_change_details(before, after)
    ]


def registration_change_details(before, after):
    if not before or not after:
        return []
    changes = []
    for field, label in CHANGE_LABELS.items():
        if before.get(field) != after.get(field):
            old_value = before.get(field)
            new_value = after.get(field)
            changes.append(
                {
                    "label": label,
                    "previous": _display_value(old_value, field),
                    "current": _display_value(new_value, field),
                }
            )
    for field, label in (
        ("competitor_items", "Competitor items"),
        ("items", "Requested products"),
        ("attachments", "Attachments"),
    ):
        if before.get(field) != after.get(field):
            changes.append({"label": label, "previous": "", "current": "Updated"})
    return changes


def _display_value(value, field=None):
    if field == "status" and value:
        # Show the registration status by its current screen name
        from .models import Registration

        if value in Registration.Status.values:
            return Registration.Status(value).label.lower()
    if value in (None, ""):
        return "Not set"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value).replace("_", " ")
