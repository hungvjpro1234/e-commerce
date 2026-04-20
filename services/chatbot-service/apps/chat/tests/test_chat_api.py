from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase


class ChatAPITests(APITestCase):
    @patch("apps.chat.views.get_chatbot_service")
    def test_chat_endpoint_returns_grounded_answer(self, get_service):
        service = Mock()
        service.chat.return_value = {
            "answer": "I found similar options in Cloth: Demo Hoodie, Streetwear Hoodie.",
            "evidence": [
                {"type": "product", "id": "p-1", "title": "Demo Hoodie", "domain": "cloth"},
                {"type": "product", "id": "p-2", "title": "Streetwear Hoodie", "domain": "cloth"},
            ],
            "context_summary": {"intent": "similar_item", "domain": "cloth", "record_count": 2},
            "debug": {"query_trace": ["similar_products_by_category"]},
        }
        get_service.return_value = service

        response = self.client.post(
            "/api/chat",
            {
                "message": "Show me similar items",
                "context": {"domain": "cloth", "product_id": "p-0", "page_context": "product_detail"},
                "debug": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["evidence"])
        service.chat.assert_called_once()

    @patch("apps.chat.views.get_chatbot_service")
    def test_chat_context_endpoint_returns_evidence_summary(self, get_service):
        service = Mock()
        service.context.return_value = {
            "intent": "product_discovery",
            "domain": "laptop",
            "evidence": [{"type": "product", "id": "p-1", "title": "Dell XPS 15"}],
            "record_count": 1,
            "query_trace": ["domain_product_lookup"],
        }
        get_service.return_value = service

        response = self.client.post(
            "/api/chat/context",
            {
                "message": "Recommend a laptop",
                "context": {"domain": "laptop"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["intent"], "product_discovery")
        service.context.assert_called_once()
