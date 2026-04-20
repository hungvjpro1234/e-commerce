from pathlib import Path

import torch
from django.conf import settings

from apps.recommendations.product_gateway import ProductCatalogGateway
from apps.recommendations.training import BehaviorMLP


class RecommendationEngine:
    def __init__(self):
        self.catalog = ProductCatalogGateway()

    def _load_artifact(self):
        artifact_path = Path(settings.MODEL_ARTIFACT_PATH)
        if not artifact_path.exists():
            return None
        return torch.load(artifact_path, map_location="cpu")

    def _catalog_index(self):
        indexed = {}
        for item in self.catalog.list_all():
            indexed[f"{item['domain']}::{item['id']}"] = item
        return indexed

    def recommend(self, *, user_id, limit=6, domain="", product_id=""):
        limit = max(1, limit)
        artifact = self._load_artifact()
        catalog_index = self._catalog_index()
        if not artifact:
            return self._popularity_fallback(catalog_index, limit=limit, domain=domain, exclude_product_id=product_id)

        user_to_idx = artifact.get("user_to_idx", {})
        item_to_idx = artifact.get("item_to_idx", {})
        if user_id not in user_to_idx or not item_to_idx:
            return self._popularity_fallback(catalog_index, limit=limit, domain=domain, exclude_product_id=product_id)

        model = BehaviorMLP(max(len(user_to_idx), 1), max(len(item_to_idx), 1))
        model.load_state_dict(artifact["state_dict"])
        model.eval()

        user_index = torch.tensor([user_to_idx[user_id]] * len(item_to_idx), dtype=torch.long)
        item_indices = torch.tensor(list(range(len(item_to_idx))), dtype=torch.long)
        with torch.no_grad():
            scores = model(user_index, item_indices).tolist()

        reverse_items = {idx: key for key, idx in item_to_idx.items()}
        ranked = []
        for idx, score in enumerate(scores):
            item_key = reverse_items[idx]
            product = catalog_index.get(item_key)
            if not product:
                continue
            if domain and product.get("domain") != domain:
                continue
            if product_id and str(product.get("id")) == str(product_id):
                continue
            ranked.append(self._serialize_item(product, float(score)))

        ranked.sort(key=lambda item: item["score"], reverse=True)
        if ranked:
            return {"items": ranked[:limit], "model_source": "model_behavior"}
        return self._popularity_fallback(catalog_index, limit=limit, domain=domain, exclude_product_id=product_id)

    def _popularity_fallback(self, catalog_index, *, limit, domain="", exclude_product_id=""):
        artifact = self._load_artifact() or {}
        popularity = artifact.get("popularity", {})
        ranked = []
        for item_key, product in catalog_index.items():
            if domain and product.get("domain") != domain:
                continue
            if exclude_product_id and str(product.get("id")) == str(exclude_product_id):
                continue
            ranked.append(self._serialize_item(product, float(popularity.get(item_key, 0.0))))
        ranked.sort(key=lambda item: (item["score"], item.get("name", "")), reverse=True)
        return {"items": ranked[:limit], "model_source": "popularity_fallback"}

    def _serialize_item(self, product, score):
        return {
            "product_id": str(product.get("id")),
            "product_service": product.get("domain"),
            "score": round(score, 4),
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "price": str(product.get("price", "")),
            "domain": product.get("domain", ""),
            "domain_label": product.get("domain_label", ""),
            "image_url": product.get("image_url", ""),
        }
