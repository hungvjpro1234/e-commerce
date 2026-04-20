from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer


class CustomerAuthTests(APITestCase):
    def test_customer_can_register_and_login(self):
        register_response = self.client.post(
            "/api/customers/register",
            {
                "email": "customer@example.com",
                "full_name": "Customer One",
                "password": "strongpass123",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)

        login_response = self.client.post(
            "/api/customers/login",
            {
                "email": "customer@example.com",
                "password": "strongpass123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["data"]["user"]["role"], "customer")

    def test_profile_requires_customer_token(self):
        response = self.client.get("/api/customers/profile")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
