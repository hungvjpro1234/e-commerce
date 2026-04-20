import argparse
import ast
import csv
import random
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG, PRODUCT_DOMAIN_ORDER


BEHAVIOR_TYPES = (
    "register",
    "login",
    "search",
    "view_product",
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "purchase",
)

CSV_FIELDS = [
    "user_id",
    "session_id",
    "timestamp",
    "behavior_type",
    "product_service",
    "product_id",
    "category",
    "search_keyword",
    "quantity",
    "step_in_session",
    "label_next_behavior",
    "source_service",
    "is_synthetic",
]

DEFAULT_OUTPUT = ROOT_DIR / "docs" / "sample-data" / "data_user500.csv"
DEFAULT_SAMPLE_OUTPUT = ROOT_DIR / "docs" / "sample-data" / "data_user500_sample20.csv"
UUID_NAMESPACE = uuid.UUID("9fcae650-8d6b-4d39-8af7-b8f2dbe4c5c1")


SESSION_TEMPLATES = (
    ("register", "login", "search", "view_product", "add_to_cart", "purchase"),
    ("register", "login", "search", "view_product", "add_to_cart", "update_cart_quantity", "purchase"),
    ("login", "search", "view_product", "add_to_cart", "remove_from_cart"),
    ("login", "search", "view_product", "view_product", "add_to_cart", "purchase"),
    ("login", "search", "add_to_cart", "update_cart_quantity", "purchase"),
    ("login", "search", "view_product"),
)

REGISTER_TEMPLATES = tuple(template for template in SESSION_TEMPLATES if "register" in template)
RETURNING_USER_TEMPLATES = tuple(template for template in SESSION_TEMPLATES if "register" not in template)

SEARCH_KEYWORDS_BY_DOMAIN = {
    "cloth": ["hoodie", "jacket", "dress", "tee"],
    "laptop": ["ultrabook", "gaming laptop", "business laptop", "oled laptop"],
    "mobile": ["android phone", "iphone", "camera phone", "gaming phone"],
    "accessory": ["wireless mouse", "usb hub", "keyboard", "charger"],
    "home-appliance": ["air fryer", "blender", "vacuum", "rice cooker"],
    "book": ["self help", "novel", "python book", "design patterns"],
    "beauty": ["serum", "cleanser", "sunscreen", "moisturizer"],
    "food": ["snack", "coffee", "protein bar", "tea"],
    "sports": ["yoga mat", "dumbbell", "running shoes", "football"],
    "gaming": ["mechanical keyboard", "gaming headset", "controller", "gaming mouse"],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate data_user500.csv for behavior-model training.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--sample-output", default=str(DEFAULT_SAMPLE_OUTPUT))
    parser.add_argument("--real-events-csv", default="")
    parser.add_argument("--target-users", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260420)
    return parser.parse_args()


def load_seed_products(seed_path):
    tree = ast.parse(seed_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PRODUCTS":
                    return ast.literal_eval(node.value)
    return []


def build_product_catalog():
    catalog = []
    for domain in PRODUCT_DOMAIN_ORDER:
        seed_path = (
            ROOT_DIR
            / "services"
            / f"{domain}-service"
            / "apps"
            / "products"
            / "management"
            / "commands"
            / "seed_products.py"
        )
        rows = load_seed_products(seed_path) if seed_path.exists() else []
        category = PRODUCT_DOMAIN_CONFIG[domain]["label"]
        for index, row in enumerate(rows, start=1):
            name = row[0]
            product_uuid = uuid.uuid5(UUID_NAMESPACE, f"{domain}:{name}")
            catalog.append(
                {
                    "product_service": domain,
                    "product_id": str(product_uuid),
                    "product_name": name,
                    "category": category,
                    "product_index": index,
                }
            )
    return catalog


def load_real_events_csv(path):
    rows = []
    if not path:
        return rows

    csv_path = Path(path)
    if not csv_path.exists():
        return rows

    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        synthetic_session_counter = defaultdict(int)
        for raw in reader:
            user_id = raw.get("user_id", "").strip()
            if not user_id:
                continue

            session_id = raw.get("session_id", "").strip()
            if not session_id:
                synthetic_session_counter[user_id] += 1
                session_id = f"real-{user_id}-{synthetic_session_counter[user_id]}"

            rows.append(
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": raw.get("occurred_at", "").strip() or raw.get("timestamp", "").strip(),
                    "behavior_type": raw.get("event_type", "").strip(),
                    "product_service": raw.get("product_service", "").strip(),
                    "product_id": raw.get("product_id", "").strip(),
                    "category": raw.get("category", "").strip(),
                    "search_keyword": raw.get("search_keyword", "").strip(),
                    "quantity": raw.get("quantity", "").strip(),
                    "source_service": raw.get("source_service", "").strip() or "behavior-service",
                    "is_synthetic": "0",
                }
            )
    return rows


def choose_product(rng, catalog, domain=None):
    options = catalog
    if domain:
        options = [item for item in catalog if item["product_service"] == domain]
    return rng.choice(options)


def build_search_keyword(rng, product):
    domain = product["product_service"]
    domain_keywords = SEARCH_KEYWORDS_BY_DOMAIN[domain]
    product_keywords = [token.lower() for token in product["product_name"].replace("-", " ").split() if len(token) > 3]
    candidate_keywords = domain_keywords + product_keywords
    return rng.choice(candidate_keywords)


def generate_synthetic_events(*, existing_user_ids, target_users, seed, catalog):
    rng = random.Random(seed)
    rows = []
    synthetic_users_needed = max(0, target_users - len(existing_user_ids))
    base_time = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    for user_index in range(synthetic_users_needed):
        user_id = str(uuid.uuid5(UUID_NAMESPACE, f"synthetic-user-{user_index + 1}"))
        session_count = rng.choice((2, 2, 3))
        user_start = base_time + timedelta(days=user_index % 120, hours=rng.randint(0, 10))
        is_new_user = user_index < int(target_users * 0.6)
        used_register = False

        for session_number in range(1, session_count + 1):
            if is_new_user and not used_register and session_number == 1:
                session_template = list(rng.choice(REGISTER_TEMPLATES))
            else:
                session_template = list(rng.choice(RETURNING_USER_TEMPLATES))

            session_domain = rng.choice(PRODUCT_DOMAIN_ORDER)
            current_product = choose_product(rng, catalog, session_domain)
            session_id = str(uuid.uuid5(UUID_NAMESPACE, f"{user_id}:session:{session_number}"))
            session_start = user_start + timedelta(days=session_number - 1, hours=rng.randint(0, 5))
            minute_offset = 0

            for step_index, behavior_type in enumerate(session_template, start=1):
                minute_offset += rng.randint(3, 11)
                timestamp = session_start + timedelta(minutes=minute_offset)
                row = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": timestamp.isoformat(),
                    "behavior_type": behavior_type,
                    "product_service": "",
                    "product_id": "",
                    "category": "",
                    "search_keyword": "",
                    "quantity": "",
                    "source_service": "customer-service" if behavior_type in {"register", "login", "add_to_cart", "update_cart_quantity", "remove_from_cart", "purchase"} else "web-service",
                    "is_synthetic": "1",
                }

                if behavior_type == "register":
                    used_register = True

                if behavior_type == "search":
                    row["category"] = current_product["category"]
                    row["search_keyword"] = build_search_keyword(rng, current_product)

                if behavior_type in {"view_product", "add_to_cart", "update_cart_quantity", "remove_from_cart", "purchase"}:
                    if behavior_type == "view_product" and rng.random() < 0.35:
                        current_product = choose_product(rng, catalog, session_domain)
                    row["product_service"] = current_product["product_service"]
                    row["product_id"] = current_product["product_id"]
                    row["category"] = current_product["category"]

                if behavior_type in {"add_to_cart", "update_cart_quantity", "remove_from_cart", "purchase"}:
                    row["quantity"] = str(rng.randint(1, 3))

                rows.append(row)

    return rows


def annotate_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["session_id"]].append(row)

    annotated = []
    for session_rows in grouped.values():
        session_rows.sort(key=lambda item: item["timestamp"])
        for index, row in enumerate(session_rows, start=1):
            next_behavior = session_rows[index]["behavior_type"] if index < len(session_rows) else ""
            row["step_in_session"] = str(index)
            row["label_next_behavior"] = next_behavior
            annotated.append(row)

    annotated.sort(key=lambda item: (item["timestamp"], item["user_id"], item["session_id"]))
    return annotated


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_dataset(args):
    catalog = build_product_catalog()
    real_rows = load_real_events_csv(args.real_events_csv)
    real_user_ids = {row["user_id"] for row in real_rows}
    synthetic_rows = generate_synthetic_events(
        existing_user_ids=real_user_ids,
        target_users=args.target_users,
        seed=args.seed,
        catalog=catalog,
    )
    all_rows = annotate_rows(real_rows + synthetic_rows)
    return all_rows


def summarize(rows):
    behavior_counts = defaultdict(int)
    user_ids = set()
    for row in rows:
        behavior_counts[row["behavior_type"]] += 1
        user_ids.add(row["user_id"])
    return {
        "row_count": len(rows),
        "user_count": len(user_ids),
        "behavior_counts": dict(sorted(behavior_counts.items())),
    }


def main():
    args = parse_args()
    rows = build_dataset(args)
    summary = summarize(rows)

    if summary["user_count"] < args.target_users:
        raise SystemExit(f"Dataset has only {summary['user_count']} users, expected at least {args.target_users}.")

    missing_behaviors = [behavior for behavior in BEHAVIOR_TYPES if behavior not in summary["behavior_counts"]]
    if missing_behaviors:
        raise SystemExit(f"Dataset is missing behavior types: {', '.join(missing_behaviors)}")

    output_path = Path(args.output)
    sample_output_path = Path(args.sample_output)
    write_csv(output_path, rows)
    write_csv(sample_output_path, rows[:20])

    print(f"Generated dataset: {output_path}")
    print(f"Generated sample: {sample_output_path}")
    print(f"Users: {summary['user_count']}")
    print(f"Rows: {summary['row_count']}")
    for behavior, count in summary["behavior_counts"].items():
        print(f"{behavior}: {count}")


if __name__ == "__main__":
    main()
