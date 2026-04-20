from rest_framework import status
from rest_framework.test import APITestCase

from apps.staff_accounts.models import StaffUser


class StaffAuthTests(APITestCase):
    def test_staff_can_register_and_login(self):
        register_response = self.client.post(
            "/api/staff/register",
            {
                "email": "admin@example.com",
                "full_name": "Admin User",
                "password": "strongpass123",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StaffUser.objects.count(), 1)

        login_response = self.client.post(
            "/api/staff/login",
            {
                "email": "admin@example.com",
                "password": "strongpass123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["data"]["user"]["role"], "manager")

    def test_profile_requires_valid_staff_token(self):
        response = self.client.get("/api/staff/profile")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
