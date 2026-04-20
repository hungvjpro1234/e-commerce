import argparse
import ast
import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from uuid import UUID, uuid5
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[3]
SERVICE_DIR = Path(__file__).resolve().parents[1]
for path in (ROOT_DIR, SERVICE_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG, PRODUCT_DOMAIN_ORDER


DEFAULT_DATASET_PATH = ROOT_DIR / "docs" / "sample-data" / "data_user500.csv"
DEFAULT_SUMMARY_PATH = ROOT_DIR / "services" / "chatbot-service" / "artifacts" / "kb_graph_import_summary.json"
DEFAULT_QUERY_PATH = ROOT_DIR / "docs" / "sample-data" / "kb_graph_queries.cypher"
UUID_NAMESPACE = UUID("9fcae650-8d6b-4d39-8af7-b8f2dbe4c5c1")


def parse_args():
    parser = argparse.ArgumentParser(description="Import e-commerce KB graph into Neo4j.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--query-output", default=str(DEFAULT_QUERY_PATH))
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", "http://localhost:7474"))
    parser.add_argument("--neo4j-username", default=os.getenv("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", "neo4jpassword"))
    parser.add_argument("--neo4j-database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--skip-sync", action="store_true", help="Build graph payloads but do not send them to Neo4j.")
    return parser.parse_args()


def load_behavior_rows(dataset_path):
    with Path(dataset_path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_domain_or_category(value):
    cleaned = (value or "").strip()
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    if lowered in PRODUCT_DOMAIN_CONFIG:
        return lowered

    for domain, config in PRODUCT_DOMAIN_CONFIG.items():
        if cleaned == config["label"] or lowered == config["label"].lower():
            return domain
    return ""


def fetch_product_catalog():
    catalog = build_seed_product_catalog()
    session = requests.Session()
    for domain in PRODUCT_DOMAIN_ORDER:
        config = PRODUCT_DOMAIN_CONFIG[domain]
        base_url = os.getenv(config["service_url_setting"], f"http://{config['service_name']}:8000")
        url = f"{base_url}/api/{config['resource']}"
        try:
            response = session.get(url, timeout=8)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            payload = []

        for item in payload:
            catalog[str(item["id"])] = {
                "product_id": str(item["id"]),
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "price": str(item.get("price", "")),
                "stock": item.get("stock"),
                "image_url": item.get("image_url", ""),
                "domain": domain,
                "domain_label": config["label"],
            }
    return catalog


def load_seed_products(seed_path):
    tree = ast.parse(seed_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PRODUCTS":
                    return ast.literal_eval(node.value)
    return []


def build_seed_product_catalog():
    catalog = {}
    for domain in PRODUCT_DOMAIN_ORDER:
        config = PRODUCT_DOMAIN_CONFIG[domain]
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
        if not seed_path.exists():
            continue

        for row in load_seed_products(seed_path):
            name = row[0]
            description = row[1] if len(row) > 1 else ""
            price = row[2] if len(row) > 2 else ""
            stock = row[3] if len(row) > 3 else ""
            product_id = str(uuid5(UUID_NAMESPACE, f"{domain}:{name}"))
            catalog[product_id] = {
                "product_id": product_id,
                "name": name,
                "description": description,
                "price": str(price),
                "stock": stock,
                "image_url": f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                "domain": domain,
                "domain_label": config["label"],
            }
    return catalog


def build_graph_documents(rows, product_catalog):
    users = {}
    categories = {}
    products = {}
    behaviors = []
    interest_scores = Counter()

    for row in rows:
        user_id = row["user_id"]
        session_id = row["session_id"]
        step_in_session = row["step_in_session"]
        behavior_id = f"{session_id}:{step_in_session}"
        behavior_type = row["behavior_type"]
        domain = row["product_service"].strip()
        product_id = row["product_id"].strip()
        category_name = row["category"].strip()

        users[user_id] = {"user_id": user_id}

        if category_name:
            categories[category_name] = {
                "name": category_name,
                "domain": normalize_domain_or_category(category_name),
            }
            interest_scores[(user_id, category_name)] += 1

        if product_id:
            product_meta = product_catalog.get(product_id, {})
            products[product_id] = {
                "product_id": product_id,
                "name": product_meta.get("name", ""),
                "description": product_meta.get("description", ""),
                "price": product_meta.get("price", ""),
                "stock": product_meta.get("stock"),
                "image_url": product_meta.get("image_url", ""),
                "domain": domain or product_meta.get("domain", ""),
                "category": category_name or product_meta.get("domain_label", ""),
            }

        behaviors.append(
            {
                "behavior_id": behavior_id,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": row["timestamp"],
                "behavior_type": behavior_type,
                "product_id": product_id,
                "product_service": domain,
                "category": category_name,
                "search_keyword": row["search_keyword"].strip(),
                "quantity": int(row["quantity"]) if row["quantity"].strip() else None,
                "source_service": row["source_service"].strip(),
                "is_synthetic": row["is_synthetic"].strip() == "1",
            }
        )

    interests = [
        {"user_id": user_id, "category": category, "score": score}
        for (user_id, category), score in sorted(interest_scores.items())
    ]

    return {
        "users": list(users.values()),
        "categories": list(categories.values()),
        "products": list(products.values()),
        "behaviors": behaviors,
        "interests": interests,
    }


class Neo4jHttpClient:
    def __init__(self, *, uri, username, password, database):
        self.uri = uri.rstrip("/")
        self.database = database
        self.session = requests.Session()
        self.session.auth = (username, password)

    def run(self, statement, parameters=None):
        response = self.session.post(
            f"{self.uri}/db/{self.database}/tx/commit",
            json={"statements": [{"statement": statement, "parameters": parameters or {}}]},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        errors = payload.get("errors", [])
        if errors:
            raise RuntimeError(errors[0]["message"])
        return payload

    def wait_until_ready(self, retries=20, delay_seconds=3):
        last_error = None
        for _ in range(retries):
            try:
                self.run("RETURN 1 AS ready")
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(delay_seconds)
        raise RuntimeError(f"Neo4j is not ready: {last_error}")


def create_constraints(client):
    statements = [
        "CREATE CONSTRAINT user_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT product_product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT behavior_behavior_id IF NOT EXISTS FOR (b:Behavior) REQUIRE b.behavior_id IS UNIQUE",
    ]
    for statement in statements:
        client.run(statement)


def import_documents(client, documents):
    client.run(
        """
        UNWIND $rows AS row
        MERGE (:Category {name: row.name})
        """,
        {"rows": documents["categories"]},
    )
    client.run(
        """
        UNWIND $rows AS row
        MERGE (p:Product {product_id: row.product_id})
        SET p.name = row.name,
            p.description = row.description,
            p.price = row.price,
            p.stock = row.stock,
            p.image_url = row.image_url,
            p.domain = row.domain,
            p.category = row.category
        WITH p, row
        FOREACH (_ IN CASE WHEN row.category <> '' THEN [1] ELSE [] END |
            MERGE (c:Category {name: row.category})
            MERGE (p)-[:BELONGS_TO]->(c)
        )
        """,
        {"rows": documents["products"]},
    )
    client.run(
        """
        UNWIND $rows AS row
        MERGE (:User {user_id: row.user_id})
        """,
        {"rows": documents["users"]},
    )
    client.run(
        """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row.user_id})
        MERGE (b:Behavior {behavior_id: row.behavior_id})
        SET b.behavior_type = row.behavior_type,
            b.timestamp = row.timestamp,
            b.session_id = row.session_id,
            b.search_keyword = row.search_keyword,
            b.quantity = row.quantity,
            b.source_service = row.source_service,
            b.is_synthetic = row.is_synthetic,
            b.product_service = row.product_service
        MERGE (u)-[:PERFORMED]->(b)
        FOREACH (_ IN CASE WHEN row.category <> '' THEN [1] ELSE [] END |
            MERGE (c:Category {name: row.category})
            MERGE (b)-[:IN_CATEGORY]->(c)
        )
        FOREACH (_ IN CASE WHEN row.product_id <> '' THEN [1] ELSE [] END |
            MERGE (p:Product {product_id: row.product_id})
            MERGE (b)-[:ON_PRODUCT]->(p)
        )
        """,
        {"rows": documents["behaviors"]},
    )
    client.run(
        """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row.user_id})
        MERGE (c:Category {name: row.category})
        MERGE (u)-[r:INTERESTED_IN]->(c)
        SET r.score = row.score
        """,
        {"rows": documents["interests"]},
    )


def verify_graph_counts(client):
    query = """
    CALL {
      MATCH (u:User)
      RETURN count(u) AS users
    }
    CALL {
      MATCH (c:Category)
      RETURN count(c) AS categories
    }
    CALL {
      MATCH (p:Product)
      RETURN count(p) AS products
    }
    CALL {
      MATCH (b:Behavior)
      RETURN count(b) AS behaviors
    }
    CALL {
      MATCH (:User)-[r:PERFORMED]->(:Behavior)
      RETURN count(r) AS performed
    }
    CALL {
      MATCH (:Behavior)-[r:ON_PRODUCT]->(:Product)
      RETURN count(r) AS on_product
    }
    CALL {
      MATCH (:Behavior)-[r:IN_CATEGORY]->(:Category)
      RETURN count(r) AS in_category
    }
    CALL {
      MATCH (:User)-[r:INTERESTED_IN]->(:Category)
      RETURN count(r) AS interested_in
    }
    CALL {
      MATCH (:Product)-[r:BELONGS_TO]->(:Category)
      RETURN count(r) AS belongs_to
    }
    RETURN users, categories, products, behaviors, performed, on_product, in_category, interested_in, belongs_to
    """
    payload = client.run(query)
    row = payload["results"][0]["data"][0]["row"]
    return {
        "node_counts": {
            "users": row[0],
            "categories": row[1],
            "products": row[2],
            "behaviors": row[3],
        },
        "relationship_counts": {
            "performed": row[4],
            "on_product": row[5],
            "in_category": row[6],
            "interested_in": row[7],
            "belongs_to": row[8],
        },
    }


def write_sample_queries(path):
    queries = """// Top categories by user interest
MATCH (:User)-[r:INTERESTED_IN]->(c:Category)
RETURN c.name AS category, SUM(r.score) AS total_interest
ORDER BY total_interest DESC
LIMIT 10;

// Most purchased products
MATCH (u:User)-[:PERFORMED]->(b:Behavior {behavior_type: 'purchase'})-[:ON_PRODUCT]->(p:Product)
RETURN p.name AS product, COUNT(*) AS purchase_count
ORDER BY purchase_count DESC
LIMIT 10;

// Search-to-purchase path for one user
MATCH (u:User {user_id: $user_id})-[:PERFORMED]->(b:Behavior)
RETURN b.session_id, b.behavior_type, b.timestamp, b.search_keyword
ORDER BY b.timestamp ASC;

// Products linked to a category
MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category})
RETURN p.name, p.price, p.stock
ORDER BY p.name ASC
LIMIT 20;

// Users interested in the same category as a product
MATCH (p:Product {product_id: $product_id})-[:BELONGS_TO]->(c:Category)<-[r:INTERESTED_IN]-(u:User)
RETURN c.name AS category, u.user_id AS user_id, r.score AS score
ORDER BY score DESC
LIMIT 20;
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(queries, encoding="utf-8")


def write_summary(path, documents, synced, verified_counts=None):
    summary = {
        "dataset": str(DEFAULT_DATASET_PATH),
        "synced_to_neo4j": synced,
        "node_counts": {
            "users": len(documents["users"]),
            "categories": len(documents["categories"]),
            "products": len(documents["products"]),
            "behaviors": len(documents["behaviors"]),
        },
        "relationship_counts": {
            "performed": len(documents["behaviors"]),
            "on_product": sum(1 for item in documents["behaviors"] if item["product_id"]),
            "in_category": sum(1 for item in documents["behaviors"] if item["category"]),
            "interested_in": len(documents["interests"]),
            "belongs_to": len(documents["products"]),
        },
    }
    if verified_counts:
        summary["verified_counts"] = verified_counts
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    args = parse_args()
    rows = load_behavior_rows(args.dataset)
    product_catalog = fetch_product_catalog()
    documents = build_graph_documents(rows, product_catalog)
    write_sample_queries(Path(args.query_output))

    synced = False
    verified_counts = None
    if not args.skip_sync:
        client = Neo4jHttpClient(
            uri=args.neo4j_uri,
            username=args.neo4j_username,
            password=args.neo4j_password,
            database=args.neo4j_database,
        )
        client.wait_until_ready()
        create_constraints(client)
        import_documents(client, documents)
        synced = True
        verified_counts = verify_graph_counts(client)

    summary = write_summary(Path(args.summary_output), documents, synced, verified_counts=verified_counts)
    print(f"KB graph summary written to: {args.summary_output}")
    print(f"Synced to Neo4j: {synced}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
