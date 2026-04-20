from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer


class CustomerAuthTests(APITestCase):
    @patch("apps.behavior_tracking.requests.post")
    def test_customer_can_register_and_login(self, behavior_post):
        behavior_response = behavior_post.return_value
        behavior_response.raise_for_status.return_value = None
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
        self.assertEqual(behavior_post.call_count, 2)
        emitted_event_types = [call.kwargs["json"]["event_type"] for call in behavior_post.call_args_list]
        self.assertEqual(emitted_event_types, ["register", "login"])

    def test_profile_requires_customer_token(self):
        response = self.client.get("/api/customers/profile")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
