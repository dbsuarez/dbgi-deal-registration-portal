import json
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from registrations.models import GeographicArea, GeographicDataset

DEFAULT_SOURCE = "https://psgc.cloud/api/v2"


def fetch_items(base_url, resource):
    request = Request(
        f"{base_url.rstrip('/')}/{resource}",
        headers={"Accept": "application/json", "User-Agent": "DBGI-Portal-PSGC-Importer/1.0"},
    )
    with urlopen(request, timeout=120) as response:
        document = json.load(response)
    items = document.get("data") if isinstance(document, dict) else document
    if not isinstance(items, list):
        raise CommandError(f"The {resource} response did not contain a data list.")
    return items


class Command(BaseCommand):
    help = "Import a versioned Philippine Standard Geographic Code snapshot."

    def add_arguments(self, parser):
        parser.add_argument("--dataset-version", required=True)
        parser.add_argument("--source-url", default=DEFAULT_SOURCE)

    @transaction.atomic
    def handle(self, *args, **options):
        version = options["dataset_version"].strip()
        source_url = options["source_url"].strip()
        if not version:
            raise CommandError("Enter a PSGC version.")

        regions = fetch_items(source_url, "regions")
        provinces = fetch_items(source_url, "provinces")
        cities = fetch_items(source_url, "cities-municipalities")

        region_codes = {item["name"].strip(): item["code"] for item in regions}
        province_codes = {
            (item["region"].strip(), item["name"].strip()): item["code"] for item in provinces
        }
        rows = []
        for item in regions:
            rows.append(
                GeographicArea(
                    code=item["code"],
                    name=item["name"].strip(),
                    level=GeographicArea.Level.REGION,
                    region_code=item["code"],
                )
            )
        for item in provinces:
            rows.append(
                GeographicArea(
                    code=item["code"],
                    name=item["name"].strip(),
                    level=GeographicArea.Level.PROVINCE,
                    region_code=region_codes[item["region"].strip()],
                    province_code=item["code"],
                )
            )
        for item in cities:
            region_name = item["region"].strip()
            province_name = (item.get("province") or "").strip()
            rows.append(
                GeographicArea(
                    code=item["code"],
                    name=item["name"].strip(),
                    level=GeographicArea.Level.CITY_MUNICIPALITY,
                    region_code=region_codes[region_name],
                    province_code=province_codes.get((region_name, province_name), ""),
                    city_municipality_code=item["code"],
                    area_type=(item.get("type") or "").strip(),
                    postal_code=str(item.get("zip_code") or "").strip(),
                )
            )
        GeographicArea.objects.update(is_active=False)
        GeographicArea.objects.bulk_create(
            rows,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=[
                "name",
                "level",
                "region_code",
                "province_code",
                "city_municipality_code",
                "area_type",
                "postal_code",
                "is_active",
            ],
        )
        GeographicDataset.objects.update(is_current=False)
        GeographicDataset.objects.update_or_create(
            version=version,
            defaults={"source_url": source_url, "is_current": True},
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(rows)} PSGC regions, provinces, cities, and municipalities "
                f"for {version}."
            )
        )
