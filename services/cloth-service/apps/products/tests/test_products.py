from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import ClothProduct
from shared.common.auth import build_jwt_payload, encode_token


class ClothProductTests(APITestCase):
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
        response = self.client.get("/api/cloth-products")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_token_can_create_product(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.staff_token}")
        response = self.client.post(
            "/api/cloth-products",
            {
                "name": "Basic Hoodie",
                "description": "Warm hoodie",
                "price": "49.99",
                "stock": 10,
                "image_url": "https://example.com/hoodie.jpg",
                "size": "M",
                "material": "Cotton",
                "color": "Black",
                "gender": "Unisex",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClothProduct.objects.count(), 1)

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
            "/api/cloth-products",
            {
                "name": "Unauthorized Hoodie",
                "price": "30.00",
                "stock": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
