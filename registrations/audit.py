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
