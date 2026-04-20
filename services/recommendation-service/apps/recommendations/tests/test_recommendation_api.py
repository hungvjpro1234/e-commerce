import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from shared.common.auth import build_jwt_payload, encode_token


def _customer_token(user_id=None):
    user_id = user_id or uuid.uuid4()
    payload = build_jwt_payload(user_id=user_id, email="customer@test.com", user_type="customer", role="user", issuer="customer-service")
    return encode_token(payload), user_id


class RecommendationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token, self.user_id = _customer_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    @patch("apps.recommendations.views.RecommendationEngine")
    def test_recommendations_endpoint(self, engine_cls):
        engine = engine_cls.return_value
        engine.recommend.return_value = {
            "items": [{
                "product_id": str(uuid.uuid4()),
                "product_service": "cloth",
                "score": 0.95,
                "name": "Demo Hoodie",
                "description": "Test",
                "price": "39.99",
                "domain": "cloth",
                "domain_label": "Cloth",
                "image_url": "",
            }],
            "model_source": "model_behavior",
        }
        response = self.client.get("/api/recommendations/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]["items"]), 1)
