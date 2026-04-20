from collections import Counter
from functools import lru_cache
from pathlib import Path

import requests
import torch
from django.conf import settings

from apps.recommendations.ml import SequenceBehaviorModel
from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG, PRODUCT_DOMAIN_ORDER


CANONICAL_BEHAVIORS = (
    "register",
    "login",
    "search",
    "view_product",
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "purchase",
)


def normalize_category(category):
    cleaned = (category or "").strip()
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    if lowered in PRODUCT_DOMAIN_CONFIG:
        return lowered
    for domain, config in PRODUCT_DOMAIN_CONFIG.items():
        if cleaned == config["label"] or lowered == config["label"].lower():
            return domain
    return ""


class RecommendationModelService:
    def __init__(self, artifact_path=None):
        self.artifact_path = Path(artifact_path or settings.RECOMMENDATION_MODEL_ARTIFACT)
        self.device = torch.device("cpu")
        self.bundle = torch.load(self.artifact_path, map_location=self.device)
        self.encoders = self.bundle["encoders"]
        self.hyperparameters = self.bundle["hyperparameters"]
        self.label_names = [
            label for label, idx in sorted(self.encoders["label_to_id"].items(), key=lambda item: item[1]) if label != "<PAD>"
        ]

        self.model = SequenceBehaviorModel(
            model_type=self.bundle["model_type"],
            behavior_vocab_size=len(self.encoders["behavior_to_id"]),
            category_vocab_size=len(self.encoders["category_to_id"]),
            product_service_vocab_size=len(self.encoders["product_service_to_id"]),
            source_service_vocab_size=len(self.encoders["source_service_to_id"]),
            embedding_dim=self.hyperparameters["embedding_dim"],
            hidden_size=self.hyperparameters["hidden_size"],
            num_classes=len(self.label_names),
            dropout=self.hyperparameters["dropout"],
        )
        self.model.load_state_dict(self.bundle["state_dict"])
        self.model.eval()

    def _encode_value(self, value, encoder):
        cleaned = (value or "").strip()
        if not cleaned:
            return encoder["<PAD>"]
        if cleaned in encoder:
            return encoder[cleaned]
        if "<UNK>" in encoder:
            return encoder["<UNK>"]
        return encoder["<PAD>"]

    def _build_sequence(self, values, encoder):
        sequence_length = self.hyperparameters["sequence_length"]
        encoded = [self._encode_value(value, encoder) for value in values[-sequence_length:]]
        padding = [encoder["<PAD>"]] * (sequence_length - len(encoded))
        return padding + encoded

    def predict(self, recent_events, top_k=3):
        sequence_length = self.hyperparameters["sequence_length"]
        recent_events = recent_events[-sequence_length:]

        behavior_ids = self._build_sequence(
            [item.get("event_type", "") for item in recent_events],
            self.encoders["behavior_to_id"],
        )
        category_ids = self._build_sequence(
            [normalize_category(item.get("category", "")) or item.get("category", "") for item in recent_events],
            self.encoders["category_to_id"],
        )
        product_service_ids = self._build_sequence(
            [item.get("product_service", "") for item in recent_events],
            self.encoders["product_service_to_id"],
        )
        source_service_ids = self._build_sequence(
            [item.get("source_service", "") for item in recent_events],
            self.encoders["source_service_to_id"],
        )
        quantities = [int(item.get("quantity") or 0) for item in recent_events][-sequence_length:]
        quantities = [0] * (sequence_length - len(quantities)) + quantities

        with torch.no_grad():
            logits = self.model(
                torch.tensor([behavior_ids], dtype=torch.long),
                torch.tensor([category_ids], dtype=torch.long),
                torch.tensor([product_service_ids], dtype=torch.long),
                torch.tensor([source_service_ids], dtype=torch.long),
                torch.tensor([quantities], dtype=torch.float32),
                torch.tensor([min(len(recent_events), sequence_length)], dtype=torch.long),
            )
            probabilities = torch.softmax(logits, dim=1)[0]

        ranked = sorted(
            [
                {
                    "event_type": self.label_names[index],
                    "probability": float(probabilities[index].item()),
                }
                for index in range(len(self.label_names))
            ],
            key=lambda item: item["probability"],
            reverse=True,
        )

        return {
            "predicted_behavior": ranked[0]["event_type"],
            "confidence": ranked[0]["probability"],
            "top_predictions": ranked[:top_k],
        }


class ProductCatalogService:
    timeout = 8

    def _request(self, method, url):
        response = requests.request(method, url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @lru_cache(maxsize=16)
    def list_products_by_domain(self, domain):
        config = PRODUCT_DOMAIN_CONFIG[domain]
        base_url = getattr(settings, config["service_url_setting"])
        payload = self._request("get", f"{base_url}/api/{config['resource']}")
        for item in payload:
            item["domain"] = domain
            item["domain_label"] = config["label"]
        return payload

    def list_all_products(self):
        products = []
        for domain in PRODUCT_DOMAIN_ORDER:
            products.extend(self.list_products_by_domain(domain))
        return products


class RecommendationService:
    def __init__(self, model_service=None, catalog_service=None):
        self.model_service = model_service or RecommendationModelService()
        self.catalog_service = catalog_service or ProductCatalogService()

    def predict_next_behavior(self, recent_events, top_k=3):
        return self.model_service.predict(recent_events, top_k=top_k)

    def _infer_domain(self, recent_events, category="", product_service=""):
        if product_service:
            return product_service

        normalized_category = normalize_category(category)
        if normalized_category:
            return normalized_category

        for event in reversed(recent_events):
            if event.get("product_service"):
                return event["product_service"]
            normalized_event_category = normalize_category(event.get("category", ""))
            if normalized_event_category:
                return normalized_event_category

        return ""

    def _score_product(self, product, *, domain, product_id, search_keyword, predicted_behavior):
        score = 0
        reasons = []
        lowered_keyword = (search_keyword or "").strip().lower()

        if domain and product.get("domain") == domain:
            score += 3
            reasons.append("same_domain")

        if product_id and str(product.get("id")) != str(product_id):
            score += 1
        elif product_id and str(product.get("id")) == str(product_id):
            score -= 5

        haystack = " ".join(
            str(product.get(field, "")) for field in ("name", "description", "brand", "author")
        ).lower()
        if lowered_keyword:
            keyword_tokens = [token for token in lowered_keyword.split() if token]
            matched_tokens = [token for token in keyword_tokens if token in haystack]
            if matched_tokens:
                score += 2 + len(matched_tokens)
                reasons.append("search_match")

        if predicted_behavior in {"view_product", "add_to_cart", "purchase", "update_cart_quantity"}:
            score += 1
            reasons.append("intent_alignment")

        stock = int(product.get("stock", 0) or 0)
        if stock > 0:
            score += 1
        return score, reasons

    def recommend_products(self, *, recent_events, top_k, search_keyword="", category="", product_service="", product_id=""):
        prediction = self.predict_next_behavior(recent_events, top_k=3)
        predicted_behavior = prediction["predicted_behavior"]
        domain = self._infer_domain(recent_events, category=category, product_service=product_service)

        if domain:
            candidates = list(self.catalog_service.list_products_by_domain(domain))
        else:
            candidates = list(self.catalog_service.list_all_products())

        scored = []
        for product in candidates:
            score, reasons = self._score_product(
                product,
                domain=domain,
                product_id=product_id,
                search_keyword=search_keyword,
                predicted_behavior=predicted_behavior,
            )
            if score <= 0:
                continue
            scored.append((score, reasons, product))

        scored.sort(key=lambda item: (item[0], item[2].get("stock", 0), item[2].get("name", "")), reverse=True)
        selected = []
        for score, reasons, product in scored[:top_k]:
            selected.append(
                {
                    "id": str(product.get("id")),
                    "name": product.get("name"),
                    "description": product.get("description", ""),
                    "price": str(product.get("price")),
                    "stock": product.get("stock"),
                    "image_url": product.get("image_url", ""),
                    "domain": product.get("domain"),
                    "domain_label": product.get("domain_label"),
                    "recommendation_score": score,
                    "reason_codes": reasons,
                }
            )

        rationale_counter = Counter(code for item in selected for code in item["reason_codes"])
        return {
            "predicted_behavior": predicted_behavior,
            "prediction_confidence": prediction["confidence"],
            "top_predictions": prediction["top_predictions"],
            "applied_domain": domain,
            "products": selected,
            "strategy": {
                "domain_preference": domain,
                "search_keyword": search_keyword,
                "reason_summary": dict(sorted(rationale_counter.items())),
            },
        }


_recommendation_service = None


def get_recommendation_service():
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service
