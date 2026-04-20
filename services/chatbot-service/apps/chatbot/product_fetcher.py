"""
Fetches product data from all product services for KB ingestion.
Each product is normalized to a flat dict that becomes a KB document.
"""

import requests
from django.conf import settings
from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG

PRODUCT_SOURCES = [
    {
        "service": "cloth",
        "base_url_setting": "CLOTH_SERVICE_URL",
        "resource": "cloth-products",
        "extra_fields": ["size", "material", "color", "gender"],
    },
    {
        "service": "laptop",
        "base_url_setting": "LAPTOP_SERVICE_URL",
        "resource": "laptop-products",
        "extra_fields": ["brand", "cpu", "ram_gb", "storage_gb", "display_size"],
    },
    {
        "service": "mobile",
        "base_url_setting": "MOBILE_SERVICE_URL",
        "resource": "mobile-products",
        "extra_fields": ["brand", "operating_system", "screen_size", "battery_mah", "camera_mp"],
    },
    {
        "service": "accessory",
        "base_url_setting": "ACCESSORY_SERVICE_URL",
        "resource": "accessory-products",
        "extra_fields": ["brand", "accessory_type", "compatibility", "wireless", "warranty_months"],
    },
    {
        "service": "home-appliance",
        "base_url_setting": "HOME_APPLIANCE_SERVICE_URL",
        "resource": "home-appliance-products",
        "extra_fields": ["brand", "power_watt", "capacity", "energy_rating", "appliance_type"],
    },
    {
        "service": "book",
        "base_url_setting": "BOOK_SERVICE_URL",
        "resource": "book-products",
        "extra_fields": ["author", "publisher", "language", "page_count", "genre"],
    },
    {
        "service": "beauty",
        "base_url_setting": "BEAUTY_SERVICE_URL",
        "resource": "beauty-products",
        "extra_fields": ["brand", "skin_type", "volume_ml", "expiry_months", "origin_country"],
    },
    {
        "service": "food",
        "base_url_setting": "FOOD_SERVICE_URL",
        "resource": "food-products",
        "extra_fields": ["brand", "weight_g", "flavor", "expiry_date", "is_organic"],
    },
    {
        "service": "sports",
        "base_url_setting": "SPORTS_SERVICE_URL",
        "resource": "sports-products",
        "extra_fields": ["brand", "sport_type", "material", "size", "target_gender"],
    },
    {
        "service": "gaming",
        "base_url_setting": "GAMING_SERVICE_URL",
        "resource": "gaming-products",
        "extra_fields": ["brand", "platform", "connectivity", "rgb_support", "warranty_months"],
    },
]


def _fetch_products(base_url: str, resource: str) -> list[dict]:
    try:
        response = requests.get(
            f"{base_url}/api/{resource}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def _build_document_sections(product: dict, service: str, extra_fields: list[str]) -> list[str]:
    label = PRODUCT_DOMAIN_CONFIG.get(service, {}).get("label", service.title())
    sections = [
        f"Category: {label}",
        f"Product name: {product.get('name', '')}",
        f"Description: {product.get('description', '') or 'No description provided.'}",
        f"Price: ${product.get('price', '')}",
        f"Stock: {product.get('stock', 0)} units",
        f"Availability: {'Active' if product.get('is_active') else 'Inactive'}",
    ]

    spec_lines = []
    for field in extra_fields:
        value = product.get(field)
        if value not in (None, ""):
            label = field.replace("_", " ").title()
            spec_lines.append(f"{label}: {value}")
    if spec_lines:
        sections.append("Specifications:\n" + "\n".join(spec_lines))

    return sections


def fetch_all_products() -> list[dict]:
    """
    Returns a list of normalized dicts ready to be stored as KB documents:
    {
        source_id: str,
        product_service: str,
        title: str,
        content: str,
    }
    """
    results = []
    for source in PRODUCT_SOURCES:
        base_url = getattr(settings, source["base_url_setting"])
        products = _fetch_products(base_url, source["resource"])

        for product in products:
            if not product.get("is_active", True):
                continue

            sections = _build_document_sections(
                product,
                source["service"],
                source["extra_fields"],
            )
            results.append(
                {
                    "source_id": str(product.get("id", "")),
                    "product_service": source["service"],
                    "title": product.get("name", "Unnamed Product"),
                    "category_label": PRODUCT_DOMAIN_CONFIG.get(source["service"], {}).get("label", source["service"].title()),
                    "content": "\n\n".join(sections),
                }
            )

    return results
