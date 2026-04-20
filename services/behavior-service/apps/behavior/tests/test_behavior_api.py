import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from apps.behavior.models import BehaviorEvent, UserItemAggregate
from shared.common.auth import build_jwt_payload, encode_token


def _customer_token(user_id=None):
    user_id = user_id or uuid.uuid4()
    payload = build_jwt_payload(user_id=user_id, email="customer@test.com", user_type="customer", role="user", issuer="customer-service")
    return encode_token(payload), user_id


class BehaviorEventApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token, self.user_id = _customer_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_track_event_creates_aggregate(self):
        response = self.client.post("/api/events", {
            "event_type": "product_view",
            "product_service": "cloth",
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
            "page_context": "product_detail",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BehaviorEvent.objects.count(), 1)
        self.assertEqual(UserItemAggregate.objects.get().view_count, 1)
