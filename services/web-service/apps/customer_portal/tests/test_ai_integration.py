import json
from unittest.mock import patch

from django.test import Client, RequestFactory, TestCase

from apps.customer_portal.views import CartView


class CustomerPortalAIIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        session = self.client.session
        session["customer_access_token"] = "token"
        session["customer_profile"] = {
            "id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
            "email": "customer@example.com",
            "full_name": "Customer One",
            "role": "customer",
        }
        session["customer_recent_behavior_events"] = [
            {
                "event_type": "login",
                "category": "",
                "product_service": "",
                "product_id": "",
                "quantity": 0,
                "source_service": "customer-service",
            }
        ]
        session.save()

    @patch("apps.customer_portal.views.get_customer_tracking_context")
    @patch("apps.customer_portal.views.emit_behavior_event")
    @patch("apps.customer_portal.views.recommendation_gw")
    @patch("apps.customer_portal.views.product_gw")
    def test_search_page_renders_recommendation_block(
        self,
        product_gw,
        recommendation_gw,
        emit_behavior_event,
        get_customer_tracking_context,
    ):
        get_customer_tracking_context.return_value = {
            "user_id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
            "session_id": "session-1",
        }
        product_gw.list_by_domain.return_value = [
            {
                "id": "cloth-1",
                "name": "Demo Hoodie",
                "domain": "cloth",
                "domain_label": "Cloth",
                "description": "Warm hoodie",
                "stock": 10,
                "price": "39.99",
            }
        ]
        recommendation_gw.recommend_products.return_value = {
            "predicted_behavior": "view_product",
            "products": [
                {
                    "id": "cloth-2",
                    "name": "Streetwear Hoodie",
                    "description": "Cotton hoodie",
                    "price": "44.99",
                    "domain": "cloth",
                    "domain_label": "Cloth",
                    "reason_codes": ["same_domain", "search_match"],
                }
            ],
        }

        response = self.client.get("/products", {"q": "hoodie", "domain": "cloth"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You may also like")
        self.assertContains(response, "Streetwear Hoodie")
        recommendation_gw.recommend_products.assert_called_once()
        emit_behavior_event.assert_called_once()

    @patch("apps.customer_portal.views.recommendation_gw")
    @patch("apps.customer_portal.views.customer_gw")
    def test_cart_page_renders_recommendations(
        self,
        customer_gw,
        recommendation_gw,
    ):
        customer_gw.cart.return_value = {
            "data": {
                "items": [
                    {
                        "id": "item-1",
                        "product_id": "cloth-1",
                        "product_service": "cloth",
                        "product_name_snapshot": "Demo Hoodie",
                        "unit_price_snapshot": "39.99",
                        "quantity": 2,
                    }
                ],
                "total_amount": "79.98",
            }
        }
        recommendation_gw.recommend_products.return_value = {
            "predicted_behavior": "add_to_cart",
            "products": [
                {
                    "id": "cloth-3",
                    "name": "Training Joggers",
                    "description": "Soft cotton joggers",
                    "price": "29.99",
                    "domain": "cloth",
                    "domain_label": "Cloth",
                    "reason_codes": ["same_domain", "intent_alignment"],
                }
            ],
        }

        request = self.factory.get("/cart")
        request.session = {
            "customer_access_token": "token",
            "customer_profile": {
                "id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
                "email": "customer@example.com",
                "full_name": "Customer One",
                "role": "customer",
            },
            "customer_recent_behavior_events": [
                {
                    "event_type": "login",
                    "category": "",
                    "product_service": "",
                    "product_id": "",
                    "quantity": 0,
                    "source_service": "customer-service",
                }
            ],
        }
        response = CartView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Suggested additions based on what is already in your cart.", response.content.decode())
        self.assertIn("Training Joggers", response.content.decode())
        recommendation_gw.recommend_products.assert_called_once()

    @patch("apps.customer_portal.views.chatbot_gw")
    def test_chat_message_proxy_returns_grounded_answer(self, chatbot_gw):
        chatbot_gw.chat.return_value = {
            "answer": "You could pair that hoodie with matching joggers.",
            "evidence": [{"type": "product", "id": "cloth-3", "title": "Training Joggers"}],
            "context_summary": {"intent": "cart_suggestion"},
        }

        response = self.client.post(
            "/chat/message",
            data=json.dumps(
                {
                    "message": "What goes well with this hoodie?",
                    "context": {"domain": "cloth", "page_context": "product_detail", "product_id": "cloth-1"},
                    "history": [{"role": "user", "text": "Show me similar items"}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["answer"], "You could pair that hoodie with matching joggers.")
        self.assertEqual(len(payload["evidence"]), 1)
        chatbot_gw.chat.assert_called_once()
