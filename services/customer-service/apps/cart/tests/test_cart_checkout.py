from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import CartItem, Order
from apps.customers.models import Customer
from shared.common.auth import build_jwt_payload, encode_token


class CartCheckoutTests(APITestCase):
    def setUp(self):
        self.customer = Customer(email="customer@example.com", full_name="Customer One")
        self.customer.set_password("strongpass123")
        self.customer.save()
        token_payload = build_jwt_payload(
            user_id=self.customer.id,
            email=self.customer.email,
            user_type="customer",
            role="customer",
            issuer="customer-service",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {encode_token(token_payload)}")

    @patch("apps.behavior_tracking.requests.post")
    @patch("apps.cart.services.ProductServiceClient")
    def test_customer_can_add_item_to_cart(self, client_cls, behavior_post):
        client = MagicMock()
        client.validate_product.return_value = {
            "exists": True,
            "sufficient_stock": True,
            "product": {
                "id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "name": "Demo Hoodie",
                "price": "39.99",
                "stock": 10,
                "image_url": "https://example.com/demo-hoodie.jpg",
                "is_active": True,
            },
        }
        client_cls.return_value = client
        behavior_post.return_value.raise_for_status.return_value = None

        response = self.client.post(
            "/api/cart/items",
            {
                "product_service": "cloth",
                "product_id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(behavior_post.call_count, 1)
        self.assertEqual(behavior_post.call_args.kwargs["json"]["event_type"], "add_to_cart")

    @patch("apps.behavior_tracking.requests.post")
    @patch("apps.cart.services.ProductServiceClient")
    def test_checkout_creates_order_and_decrements_stock(self, client_cls, behavior_post):
        client = MagicMock()
        client.validate_product.return_value = {
            "exists": True,
            "sufficient_stock": True,
            "product": {
                "id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "name": "Demo Hoodie",
                "price": "39.99",
                "stock": 10,
                "image_url": "https://example.com/demo-hoodie.jpg",
                "is_active": True,
            },
        }
        client.decrement_stock.return_value = {"message": "Stock updated."}
        client_cls.return_value = client
        behavior_post.return_value.raise_for_status.return_value = None

        add_response = self.client.post(
            "/api/cart/items",
            {
                "product_service": "cloth",
                "product_id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "quantity": 2,
            },
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)

        checkout_response = self.client.post("/api/checkout", {}, format="json")
        self.assertEqual(checkout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(client.decrement_stock.call_count, 1)
        emitted_event_types = [call.kwargs["json"]["event_type"] for call in behavior_post.call_args_list]
        self.assertEqual(emitted_event_types, ["add_to_cart", "purchase"])

    @patch("apps.behavior_tracking.requests.post")
    @patch("apps.cart.services.ProductServiceClient")
    def test_update_and_remove_cart_item_emit_behavior_events(self, client_cls, behavior_post):
        client = MagicMock()
        client.validate_product.return_value = {
            "exists": True,
            "sufficient_stock": True,
            "product": {
                "id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "name": "Demo Hoodie",
                "price": "39.99",
                "stock": 10,
                "image_url": "https://example.com/demo-hoodie.jpg",
                "is_active": True,
            },
        }
        client_cls.return_value = client
        behavior_post.return_value.raise_for_status.return_value = None

        add_response = self.client.post(
            "/api/cart/items",
            {
                "product_service": "cloth",
                "product_id": "4db0b1e5-4e83-485d-90db-37f2a8ea1a70",
                "quantity": 1,
            },
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)

        item_id = add_response.data["data"]["items"][0]["id"]

        update_response = self.client.put(
            f"/api/cart/items/{item_id}",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        remove_response = self.client.delete(f"/api/cart/items/{item_id}")
        self.assertEqual(remove_response.status_code, status.HTTP_200_OK)

        emitted_event_types = [call.kwargs["json"]["event_type"] for call in behavior_post.call_args_list]
        self.assertEqual(
            emitted_event_types,
            ["add_to_cart", "update_cart_quantity", "remove_from_cart"],
        )
