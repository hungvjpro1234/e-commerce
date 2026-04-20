from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase


class RecommendationAPITests(APITestCase):
    @patch("apps.recommendations.views.get_recommendation_service")
    def test_predict_next_behavior_endpoint_returns_prediction(self, get_service):
        service = Mock()
        service.predict_next_behavior.return_value = {
            "predicted_behavior": "view_product",
            "confidence": 0.91,
            "top_predictions": [
                {"event_type": "view_product", "probability": 0.91},
                {"event_type": "add_to_cart", "probability": 0.05},
            ],
        }
        get_service.return_value = service

        response = self.client.post(
            "/api/recommend/predict-next-behavior",
            {
                "recent_events": [
                    {"event_type": "login", "source_service": "customer-service"},
                    {"event_type": "search", "category": "cloth", "source_service": "web-service"},
                ],
                "top_k": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["predicted_behavior"], "view_product")
        service.predict_next_behavior.assert_called_once()

    @patch("apps.recommendations.views.get_recommendation_service")
    def test_recommend_products_endpoint_returns_products(self, get_service):
        service = Mock()
        service.recommend_products.return_value = {
            "predicted_behavior": "add_to_cart",
            "prediction_confidence": 0.87,
            "top_predictions": [{"event_type": "add_to_cart", "probability": 0.87}],
            "applied_domain": "cloth",
            "products": [
                {
                    "id": "product-1",
                    "name": "Demo Hoodie",
                    "description": "Warm hoodie",
                    "price": "39.99",
                    "stock": 10,
                    "image_url": "",
                    "domain": "cloth",
                    "domain_label": "Cloth",
                    "recommendation_score": 7,
                    "reason_codes": ["same_domain", "intent_alignment"],
                }
            ],
            "strategy": {
                "domain_preference": "cloth",
                "search_keyword": "hoodie",
                "reason_summary": {"same_domain": 1, "intent_alignment": 1},
            },
        }
        get_service.return_value = service

        response = self.client.post(
            "/api/recommend/products",
            {
                "recent_events": [
                    {"event_type": "search", "category": "cloth", "source_service": "web-service"},
                    {
                        "event_type": "view_product",
                        "product_service": "cloth",
                        "product_id": "abc-123",
                        "category": "cloth",
                        "source_service": "web-service",
                    },
                ],
                "search_keyword": "hoodie",
                "category": "cloth",
                "product_service": "cloth",
                "product_id": "abc-123",
                "limit": 6,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["predicted_behavior"], "add_to_cart")
        self.assertEqual(len(response.data["data"]["products"]), 1)
        service.recommend_products.assert_called_once()
