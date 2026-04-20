from unittest.mock import patch

from django.test import Client, TestCase


class CustomerPortalBehaviorTrackingTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["customer_access_token"] = "token"
        session["customer_profile"] = {
            "id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
            "email": "customer@example.com",
            "full_name": "Customer One",
            "role": "customer",
        }
        session.save()

    @patch("apps.customer_portal.views.get_customer_tracking_context")
    @patch("apps.customer_portal.views.emit_behavior_event")
    @patch("apps.customer_portal.views.product_gw")
    def test_search_view_emits_search_event_for_logged_in_customer(
        self,
        product_gw,
        emit_behavior_event,
        get_customer_tracking_context,
    ):
        get_customer_tracking_context.return_value = {
            "user_id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
            "session_id": "",
        }
        product_gw.list_by_domain.return_value = [
            {
                "id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "name": "Demo Hoodie",
                "domain": "cloth",
                "domain_label": "Cloth",
                "description": "Warm hoodie",
                "stock": 10,
                "price": "39.99",
            }
        ]

        response = self.client.get("/products", {"q": "hoodie", "domain": "cloth"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(emit_behavior_event.call_count, 1)
        payload = emit_behavior_event.call_args.kwargs
        self.assertEqual(payload["event_type"], "search")
        self.assertEqual(payload["search_keyword"], "hoodie")
        self.assertEqual(payload["category"], "cloth")

    @patch("apps.customer_portal.views.get_customer_tracking_context")
    @patch("apps.customer_portal.views.emit_behavior_event")
    @patch("apps.customer_portal.views.product_gw")
    def test_product_detail_emits_view_product_event_for_logged_in_customer(
        self,
        product_gw,
        emit_behavior_event,
        get_customer_tracking_context,
    ):
        get_customer_tracking_context.return_value = {
            "user_id": "bc93664e-c8b7-45f1-bdef-a5f01a6b7ca3",
            "session_id": "",
        }
        product_gw.detail.return_value = {
            "id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
            "name": "Demo Hoodie",
            "domain": "cloth",
            "domain_label": "Cloth",
            "description": "Warm hoodie",
            "stock": 10,
            "price": "39.99",
        }

        response = self.client.get("/products/cloth/4db0b1e5-4e83-485d-90db-37f2a8ea1a70")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(emit_behavior_event.call_count, 1)
        payload = emit_behavior_event.call_args.kwargs
        self.assertEqual(payload["event_type"], "view_product")
        self.assertEqual(payload["product_service"], "cloth")
        self.assertEqual(payload["product_id"], "4db0b1e5-4e83-485d-90db-37f2a8ea1a70")
