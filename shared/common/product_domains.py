PRODUCT_DOMAIN_CONFIG = {
    "cloth": {
        "label": "Cloth",
        "service_name": "cloth-service",
        "resource": "cloth-products",
        "service_url_setting": "CLOTH_SERVICE_URL",
        "extra_fields": [
            {"name": "size", "label": "Size", "type": "text"},
            {"name": "material", "label": "Material", "type": "text"},
            {"name": "color", "label": "Color", "type": "text"},
            {"name": "gender", "label": "Gender", "type": "text"},
        ],
        "detail_fields": [
            {"name": "size", "label": "Size"},
            {"name": "material", "label": "Material"},
            {"name": "color", "label": "Color"},
            {"name": "gender", "label": "Gender"},
        ],
    },
    "laptop": {
        "label": "Laptop",
        "service_name": "laptop-service",
        "resource": "laptop-products",
        "service_url_setting": "LAPTOP_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "cpu", "label": "CPU", "type": "text"},
            {"name": "ram_gb", "label": "RAM (GB)", "type": "number"},
            {"name": "storage_gb", "label": "Storage (GB)", "type": "number"},
            {"name": "display_size", "label": "Display Size (inches)", "type": "number"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "cpu", "label": "CPU"},
            {"name": "ram_gb", "label": "RAM", "suffix": " GB"},
            {"name": "storage_gb", "label": "Storage", "suffix": " GB"},
            {"name": "display_size", "label": "Display", "suffix": '"'},
        ],
    },
    "mobile": {
        "label": "Mobile",
        "service_name": "mobile-service",
        "resource": "mobile-products",
        "service_url_setting": "MOBILE_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "operating_system", "label": "OS", "type": "text"},
            {"name": "screen_size", "label": "Screen Size (inches)", "type": "number"},
            {"name": "battery_mah", "label": "Battery (mAh)", "type": "number"},
            {"name": "camera_mp", "label": "Camera (MP)", "type": "number"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "operating_system", "label": "OS"},
            {"name": "screen_size", "label": "Screen", "suffix": '"'},
            {"name": "battery_mah", "label": "Battery", "suffix": " mAh"},
            {"name": "camera_mp", "label": "Camera", "suffix": " MP"},
        ],
    },
    "accessory": {
        "label": "Tech Accessories",
        "service_name": "accessory-service",
        "resource": "accessory-products",
        "service_url_setting": "ACCESSORY_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "accessory_type", "label": "Accessory Type", "type": "text"},
            {"name": "compatibility", "label": "Compatibility", "type": "text"},
            {"name": "wireless", "label": "Wireless", "type": "text"},
            {"name": "warranty_months", "label": "Warranty (months)", "type": "number"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "accessory_type", "label": "Type"},
            {"name": "compatibility", "label": "Compatibility"},
            {"name": "wireless", "label": "Wireless"},
            {"name": "warranty_months", "label": "Warranty", "suffix": " months"},
        ],
    },
    "home-appliance": {
        "label": "Home Appliances",
        "service_name": "home-appliance-service",
        "resource": "home-appliance-products",
        "service_url_setting": "HOME_APPLIANCE_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "power_watt", "label": "Power (W)", "type": "number"},
            {"name": "capacity", "label": "Capacity", "type": "text"},
            {"name": "energy_rating", "label": "Energy Rating", "type": "text"},
            {"name": "appliance_type", "label": "Appliance Type", "type": "text"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "power_watt", "label": "Power", "suffix": " W"},
            {"name": "capacity", "label": "Capacity"},
            {"name": "energy_rating", "label": "Energy Rating"},
            {"name": "appliance_type", "label": "Type"},
        ],
    },
    "book": {
        "label": "Books",
        "service_name": "book-service",
        "resource": "book-products",
        "service_url_setting": "BOOK_SERVICE_URL",
        "extra_fields": [
            {"name": "author", "label": "Author", "type": "text"},
            {"name": "publisher", "label": "Publisher", "type": "text"},
            {"name": "language", "label": "Language", "type": "text"},
            {"name": "page_count", "label": "Page Count", "type": "number"},
            {"name": "genre", "label": "Genre", "type": "text"},
        ],
        "detail_fields": [
            {"name": "author", "label": "Author"},
            {"name": "publisher", "label": "Publisher"},
            {"name": "language", "label": "Language"},
            {"name": "page_count", "label": "Pages"},
            {"name": "genre", "label": "Genre"},
        ],
    },
    "beauty": {
        "label": "Beauty",
        "service_name": "beauty-service",
        "resource": "beauty-products",
        "service_url_setting": "BEAUTY_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "skin_type", "label": "Skin Type", "type": "text"},
            {"name": "volume_ml", "label": "Volume (ml)", "type": "number"},
            {"name": "expiry_months", "label": "Shelf Life (months)", "type": "number"},
            {"name": "origin_country", "label": "Origin Country", "type": "text"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "skin_type", "label": "Skin Type"},
            {"name": "volume_ml", "label": "Volume", "suffix": " ml"},
            {"name": "expiry_months", "label": "Shelf Life", "suffix": " months"},
            {"name": "origin_country", "label": "Origin"},
        ],
    },
    "food": {
        "label": "Food & Drinks",
        "service_name": "food-service",
        "resource": "food-products",
        "service_url_setting": "FOOD_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "weight_g", "label": "Weight (g)", "type": "number"},
            {"name": "flavor", "label": "Flavor", "type": "text"},
            {"name": "expiry_date", "label": "Expiry Date", "type": "date"},
            {"name": "is_organic", "label": "Organic", "type": "text"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "weight_g", "label": "Weight", "suffix": " g"},
            {"name": "flavor", "label": "Flavor"},
            {"name": "expiry_date", "label": "Expiry Date"},
            {"name": "is_organic", "label": "Organic"},
        ],
    },
    "sports": {
        "label": "Sports",
        "service_name": "sports-service",
        "resource": "sports-products",
        "service_url_setting": "SPORTS_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "sport_type", "label": "Sport Type", "type": "text"},
            {"name": "material", "label": "Material", "type": "text"},
            {"name": "size", "label": "Size", "type": "text"},
            {"name": "target_gender", "label": "Target Gender", "type": "text"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "sport_type", "label": "Sport"},
            {"name": "material", "label": "Material"},
            {"name": "size", "label": "Size"},
            {"name": "target_gender", "label": "Target Gender"},
        ],
    },
    "gaming": {
        "label": "Gaming",
        "service_name": "gaming-service",
        "resource": "gaming-products",
        "service_url_setting": "GAMING_SERVICE_URL",
        "extra_fields": [
            {"name": "brand", "label": "Brand", "type": "text"},
            {"name": "platform", "label": "Platform", "type": "text"},
            {"name": "connectivity", "label": "Connectivity", "type": "text"},
            {"name": "rgb_support", "label": "RGB Support", "type": "text"},
            {"name": "warranty_months", "label": "Warranty (months)", "type": "number"},
        ],
        "detail_fields": [
            {"name": "brand", "label": "Brand"},
            {"name": "platform", "label": "Platform"},
            {"name": "connectivity", "label": "Connectivity"},
            {"name": "rgb_support", "label": "RGB Support"},
            {"name": "warranty_months", "label": "Warranty", "suffix": " months"},
        ],
    },
}

PRODUCT_DOMAIN_ORDER = tuple(PRODUCT_DOMAIN_CONFIG.keys())

PRODUCT_SERVICE_CHOICES = tuple(
    (slug, config["label"]) for slug, config in PRODUCT_DOMAIN_CONFIG.items()
)


def build_product_service_map():
    product_map = {}
    for slug, config in PRODUCT_DOMAIN_CONFIG.items():
        product_map[slug] = {
            "name": config["service_name"],
            "base_url": f"http://{config['service_name']}:8000",
            "resource": config["resource"],
            "label": config["label"],
        }
    return product_map
