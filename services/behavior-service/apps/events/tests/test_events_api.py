import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.events.models import BehaviorEvent


class BehaviorEventsAPITestCase(APITestCase):
    def setUp(self):
        self.internal_headers = {
            "HTTP_X_INTERNAL_SERVICE_TOKEN": settings.INTERNAL_SERVICE_TOKEN,
            "HTTP_X_SERVICE_NAME": "customer-service",
        }

    def test_ingest_event_with_internal_token(self):
        payload = {
            "user_id": str(uuid.uuid4()),
            "event_type": "search",
            "category": "cloth",
            "search_keyword": "hoodie",
            "metadata": {"source": "web-service"},
        }

        response = self.client.post("/api/internal/events", payload, format="json", **self.internal_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["event_type"], "search")

        event = BehaviorEvent.objects.get()
        self.assertEqual(event.source_service, "customer-service")
        self.assertEqual(event.search_keyword, "hoodie")

    def test_ingest_rejects_invalid_internal_token(self):
        payload = {
            "user_id": str(uuid.uuid4()),
            "event_type": "login",
            "metadata": {},
        }

        response = self.client.post(
            "/api/internal/events",
            payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="wrong-token",
            HTTP_X_SERVICE_NAME="customer-service",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BehaviorEvent.objects.count(), 0)

    def test_list_and_export_events_require_internal_token_and_return_data(self):
        event = BehaviorEvent.objects.create(
            user_id=uuid.uuid4(),
            source_service="customer-service",
            event_type=BehaviorEvent.EventType.PURCHASE,
            product_service=BehaviorEvent.ProductService.CLOTH,
            product_id=uuid.uuid4(),
            quantity=1,
            metadata={"source": "customer-service"},
        )

        list_response = self.client.get("/api/events?limit=10", **self.internal_headers)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["data"]), 1)
        self.assertEqual(list_response.data["data"][0]["id"], str(event.id))

        export_response = self.client.get("/api/events/export", **self.internal_headers)
        self.assertEqual(export_response.status_code, status.HTTP_200_OK)
        self.assertEqual(export_response["Content-Type"], "text/csv")
        self.assertIn("purchase", export_response.content.decode("utf-8"))
