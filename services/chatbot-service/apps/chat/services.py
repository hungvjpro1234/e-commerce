import re
from collections import Counter

import requests
from django.conf import settings

from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG, PRODUCT_DOMAIN_ORDER


INTENT_PATTERNS = {
    "category_explanation": ("category", "what is", "explain", "meaning", "about"),
    "same_category": ("same category", "same kind", "same type"),
    "similar_item": ("similar", "like this", "related", "alternative"),
    "cart_suggestion": ("cart", "bundle", "checkout", "go with", "together"),
    "product_discovery": ("find", "looking for", "recommend", "show me", "suggest"),
}


def normalize_domain(value):
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


class Neo4jHttpClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        self.base_url = settings.NEO4J_URI.rstrip("/")

    def run(self, statement, parameters=None):
        response = self.session.post(
            f"{self.base_url}/db/{settings.NEO4J_DATABASE}/tx/commit",
            json={"statements": [{"statement": statement, "parameters": parameters or {}}]},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        errors = payload.get("errors", [])
        if errors:
            raise RuntimeError(errors[0]["message"])
        return payload["results"][0]["data"] if payload.get("results") else []


class ProductCatalogClient:
    timeout = 8

    def _request(self, url):
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_product(self, domain, product_id):
        config = PRODUCT_DOMAIN_CONFIG[domain]
        base_url = getattr(settings, config["service_url_setting"])
        payload = self._request(f"{base_url}/api/{config['resource']}/{product_id}")
        payload["domain"] = domain
        payload["domain_label"] = config["label"]
        return payload

    def list_by_domain(self, domain):
        config = PRODUCT_DOMAIN_CONFIG[domain]
        base_url = getattr(settings, config["service_url_setting"])
        payload = self._request(f"{base_url}/api/{config['resource']}")
        for item in payload:
            item["domain"] = domain
            item["domain_label"] = config["label"]
        return payload


class GraphRetriever:
    def __init__(self, neo4j_client=None, product_client=None):
        self.neo4j = neo4j_client or Neo4jHttpClient()
        self.product_client = product_client or ProductCatalogClient()

    def _query_categories(self):
        query = """
        MATCH (:User)-[r:INTERESTED_IN]->(c:Category)
        RETURN c.name AS category, SUM(r.score) AS total_interest
        ORDER BY total_interest DESC
        LIMIT 5
        """
        return [row["row"] for row in self.neo4j.run(query)]

    def _query_products_by_category(self, category, limit=5):
        query = """
        MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category})
        RETURN p.product_id, p.name, p.price, p.stock, p.domain
        ORDER BY p.stock DESC, p.name ASC
        LIMIT $limit
        """
        return [row["row"] for row in self.neo4j.run(query, {"category": category, "limit": limit})]

    def _query_similar_products(self, product_id, limit=5):
        query = """
        MATCH (p:Product {product_id: $product_id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(other:Product)
        WHERE other.product_id <> $product_id
        RETURN c.name AS category, other.product_id, other.name, other.price, other.stock, other.domain
        ORDER BY other.stock DESC, other.name ASC
        LIMIT $limit
        """
        return [row["row"] for row in self.neo4j.run(query, {"product_id": product_id, "limit": limit})]

    def _query_cart_suggestions(self, domain, limit=5):
        if not domain:
            return []
        query = """
        MATCH (b:Behavior {behavior_type: 'purchase'})-[:ON_PRODUCT]->(p:Product {domain: $domain})
        RETURN p.product_id, p.name, p.price, p.stock, p.domain, count(*) AS purchase_count
        ORDER BY purchase_count DESC, p.stock DESC
        LIMIT $limit
        """
        return [row["row"] for row in self.neo4j.run(query, {"domain": domain, "limit": limit})]

    def retrieve(self, *, message, context):
        lowered = message.lower()
        domain = normalize_domain(context.get("domain", ""))
        product_id = context.get("product_id", "")
        if not domain:
            domain = self._extract_domain_from_message(lowered)

        try:
            if product_id:
                intent = "similar_item" if any(token in lowered for token in INTENT_PATTERNS["similar_item"]) else "same_category"
                records = self._query_similar_products(product_id)
                evidence = [
                    {"type": "product", "id": row[1], "title": row[2], "domain": row[5], "category": row[0]}
                    for row in records
                ]
                return {
                    "intent": intent,
                    "domain": domain,
                    "records": records,
                    "evidence": evidence,
                    "query_trace": ["similar_products_by_category"],
                }

            if context.get("cart_product_ids"):
                records = self._query_cart_suggestions(domain)
                evidence = [
                    {"type": "product", "id": row[0], "title": row[1], "domain": row[4], "purchase_count": row[5]}
                    for row in records
                ]
                return {
                    "intent": "cart_suggestion",
                    "domain": domain,
                    "records": records,
                    "evidence": evidence,
                    "query_trace": ["cart_purchase_patterns"],
                }

            if any(token in lowered for token in INTENT_PATTERNS["category_explanation"]):
                category = PRODUCT_DOMAIN_CONFIG[domain]["label"] if domain else ""
                records = self._query_products_by_category(category, limit=5) if category else []
                evidence = [
                    {"type": "category", "id": category, "title": category},
                    *[
                        {"type": "product", "id": row[0], "title": row[1], "domain": row[4]}
                        for row in records
                    ],
                ] if category else []
                return {
                    "intent": "category_explanation",
                    "domain": domain,
                    "records": records,
                    "evidence": evidence,
                    "query_trace": ["category_products_lookup"] if category else [],
                }

            if domain:
                category_label = PRODUCT_DOMAIN_CONFIG[domain]["label"]
                records = self._query_products_by_category(category_label, limit=5)
                evidence = [
                    {"type": "product", "id": row[0], "title": row[1], "domain": row[4], "category": category_label}
                    for row in records
                ]
                return {
                    "intent": "product_discovery",
                    "domain": domain,
                    "records": records,
                    "evidence": evidence,
                    "query_trace": ["domain_product_lookup"],
                }

            category_rows = self._query_categories()
            evidence = [
                {"type": "category", "id": row[0], "title": row[0], "interest_score": row[1]}
                for row in category_rows
            ]
            return {
                "intent": "shopping_assistance",
                "domain": "",
                "records": category_rows,
                "evidence": evidence,
                "query_trace": ["top_interest_categories"],
            }
        except (requests.RequestException, RuntimeError):
            return {
                "intent": "shopping_assistance",
                "domain": domain,
                "records": [],
                "evidence": [],
                "query_trace": ["graph_unavailable"],
            }

    def _extract_domain_from_message(self, lowered_message):
        for domain, config in PRODUCT_DOMAIN_CONFIG.items():
            if domain in lowered_message or config["label"].lower() in lowered_message:
                return domain
        return ""


class GroundedAnswerService:
    def build_answer(self, *, message, retrieval_result):
        intent = retrieval_result["intent"]
        records = retrieval_result["records"]
        domain = retrieval_result["domain"]

        if not records:
            return "I could not find relevant graph context for that request yet. Try asking about a category, a product type, or items related to your cart."

        if intent == "category_explanation":
            label = PRODUCT_DOMAIN_CONFIG[domain]["label"] if domain else "this category"
            product_names = ", ".join(row[1] for row in records[:3])
            return f"{label} includes products like {product_names}. This category groups items with similar shopping intent and product attributes."

        if intent in {"similar_item", "same_category"}:
            product_names = ", ".join(row[2] for row in records[:3])
            category = records[0][0]
            return f"I found similar options in {category}: {product_names}. These items share the same category as the product you are viewing."

        if intent == "cart_suggestion":
            product_names = ", ".join(row[1] for row in records[:3])
            return f"Based on purchase patterns in this domain, you could also consider {product_names}. These items show up frequently in completed shopping flows."

        if intent == "product_discovery":
            label = PRODUCT_DOMAIN_CONFIG[domain]["label"] if domain else "the catalog"
            product_names = ", ".join(row[1] for row in records[:3])
            return f"For {label}, a good place to start is {product_names}. I selected these from the graph-backed product catalog for this shopping context."

        category_names = ", ".join(row[0] for row in records[:3])
        return f"The graph currently shows strongest user interest around {category_names}. Tell me which category or product type you want and I can narrow it down."


class ChatbotService:
    def __init__(self, retriever=None, answer_service=None):
        self.retriever = retriever or GraphRetriever()
        self.answer_service = answer_service or GroundedAnswerService()

    def chat(self, *, message, context, debug=False):
        retrieval = self.retriever.retrieve(message=message, context=context)
        answer = self.answer_service.build_answer(message=message, retrieval_result=retrieval)
        payload = {
            "answer": answer,
            "evidence": retrieval["evidence"],
            "context_summary": {
                "intent": retrieval["intent"],
                "domain": retrieval["domain"],
                "record_count": len(retrieval["records"]),
            },
        }
        if debug or settings.CHATBOT_DEBUG:
            payload["debug"] = {
                "query_trace": retrieval["query_trace"],
            }
        return payload

    def context(self, *, message, context):
        retrieval = self.retriever.retrieve(message=message, context=context)
        return {
            "intent": retrieval["intent"],
            "domain": retrieval["domain"],
            "evidence": retrieval["evidence"],
            "record_count": len(retrieval["records"]),
            "query_trace": retrieval["query_trace"],
        }


_chatbot_service = None


def get_chatbot_service():
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
