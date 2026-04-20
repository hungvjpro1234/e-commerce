"""
Integration tests for POST /api/chat.
OpenAI is mocked so no real API calls are made.
"""

import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from shared.common.auth import build_jwt_payload, encode_token


def _customer_token(user_id=None):
    user_id = user_id or uuid.uuid4()
    payload = build_jwt_payload(
        user_id=user_id,
        email="customer@test.com",
        user_type="customer",
        role="user",
        issuer="customer-service",
    )
    return encode_token(payload), user_id


class ChatViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token, self.user_id = _customer_token()

    def _auth_headers(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    @patch("apps.chatbot.rag_service._call_openai", return_value="You can return items within 30 days.")
    def test_chat_returns_answer(self, _mock_openai):
        response = self.client.post(
            "/api/chat",
            data={
                "question": "What is your return policy?",
                "domain": "beauty",
                "page_context": "product_detail",
            },
            format="json",
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data["data"])
        self.assertIn("conversation_id", data["data"])
        self.assertIn("citations", data["data"])

    def test_chat_requires_auth(self):
        response = self.client.post(
            "/api/chat",
            data={"question": "Hello"},
            format="json",
        )
        # DRF raises PermissionDenied (403) when IsCustomerUser check fails
        self.assertIn(response.status_code, [401, 403])

    def test_chat_rejects_empty_question(self):
        response = self.client.post(
            "/api/chat",
            data={"question": ""},
            format="json",
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.chatbot.rag_service._call_openai", return_value="Follow-up answer.")
    def test_chat_continues_conversation(self, _mock_openai):
        r1 = self.client.post(
            "/api/chat",
            data={"question": "What is your return policy?"},
            format="json",
            **self._auth_headers(),
        )
        conv_id = r1.json()["data"]["conversation_id"]

        r2 = self.client.post(
            "/api/chat",
            data={"question": "How long does that take?", "conversation_id": conv_id},
            format="json",
            **self._auth_headers(),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["data"]["conversation_id"], conv_id)

    @patch("apps.chatbot.rag_service._call_openai", return_value="This serum is suitable for dry skin.")
    def test_chat_accepts_product_context(self, _mock_openai):
        response = self.client.post(
            "/api/chat",
            data={
                "question": "Serum nay hop da kho khong?",
                "domain": "beauty",
                "page_context": "product_detail",
                "product_id": str(uuid.uuid4()),
            },
            format="json",
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
