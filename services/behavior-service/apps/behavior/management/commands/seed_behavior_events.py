import uuid

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.behavior.services import BehaviorTracker

PRODUCT_ENDPOINTS = [
    ("cloth", settings.CLOTH_SERVICE_URL, "cloth-products"),
    ("laptop", settings.LAPTOP_SERVICE_URL, "laptop-products"),
    ("mobile", settings.MOBILE_SERVICE_URL, "mobile-products"),
    ("accessory", settings.ACCESSORY_SERVICE_URL, "accessory-products"),
    ("beauty", settings.BEAUTY_SERVICE_URL, "beauty-products"),
    ("gaming", settings.GAMING_SERVICE_URL, "gaming-products"),
]


def _first_product(domain, base_url, resource):
    response = requests.get(f"{base_url}/api/{resource}", timeout=10)
    response.raise_for_status()
    items = response.json()
    if not items:
        return None
    return {"product_service": domain, "product_id": uuid.UUID(items[0]["id"])}


class Command(BaseCommand):
    help = "Seed sample behavior events for recommendation training."

    def handle(self, *args, **options):
        tracker = BehaviorTracker()
        catalog_items = [item for item in (_first_product(*endpoint) for endpoint in PRODUCT_ENDPOINTS) if item]
        if not catalog_items:
            raise RuntimeError("No catalog products available to seed behavior events.")

        seed_events = []
        user_a = uuid.UUID("00000000-0000-0000-0000-000000000001")
        user_b = uuid.UUID("00000000-0000-0000-0000-000000000002")
        for index, item in enumerate(catalog_items[:4]):
            seed_events.append(
                {
                    "user_id": user_a,
                    "product_service": item["product_service"],
                    "product_id": item["product_id"],
                    "event_type": "product_view",
                    "quantity": 1,
                }
            )
            if index < 3:
                seed_events.append(
                    {
                        "user_id": user_a,
                        "product_service": item["product_service"],
                        "product_id": item["product_id"],
                        "event_type": "cart_add",
                        "quantity": 1,
                    }
                )
        best_item = catalog_items[0]
        seed_events.append(
            {
                "user_id": user_a,
                "product_service": best_item["product_service"],
                "product_id": best_item["product_id"],
                "event_type": "purchase",
                "quantity": 1,
            }
        )
        if len(catalog_items) > 1:
            seed_events.append(
                {
                    "user_id": user_b,
                    "product_service": catalog_items[1]["product_service"],
                    "product_id": catalog_items[1]["product_id"],
                    "event_type": "product_view",
                    "quantity": 1,
                }
            )
        for event in seed_events:
            tracker.track_event(**event)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(seed_events)} behavior events."))
