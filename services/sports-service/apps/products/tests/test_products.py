from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import SportsProduct
from shared.common.auth import build_jwt_payload, encode_token


class SportsProductTests(APITestCase):
    def setUp(self):
        payload = build_jwt_payload(
            user_id="staff-1",
            email="admin@example.com",
            user_type="staff",
            role="manager",
            issuer="staff-service",
        )
        self.staff_token = encode_token(payload)

    def test_public_can_list_products(self):
        response = self.client.get("/api/sports-products")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_token_can_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.staff_token}")
        response = self.client.post(
            "/api/sports-products",
            {
                "name": "Demo Product",
                "description": "Created from automated test",
                "price": "49.99",
                "stock": 10,
                "image_url": "https://example.com/demo.jpg",
                "brand": 'Nike',
                "sport_type": 'Running',
                "material": 'Polyester',
                "size": 'M',
                "target_gender": 'Unisex'
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SportsProduct.objects.count(), 1)

    def test_customer_token_cannot_create_product(self):
        payload = build_jwt_payload(
            user_id="customer-1",
            email="customer@example.com",
            user_type="customer",
            role="customer",
            issuer="customer-service",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {encode_token(payload)}")
        response = self.client.post(
            "/api/sports-products",
            {
                "name": "Unauthorized Product",
                "price": "30.00",
                "stock": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
