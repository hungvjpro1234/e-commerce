from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.staff_accounts.models import StaffUser
from apps.staff_accounts.serializers import (
    StaffLoginSerializer,
    StaffProfileSerializer,
    StaffRegisterSerializer,
)
from apps.staff_accounts.services import issue_staff_token
from shared.common.permissions import IsStaffUser
from shared.common.responses import fail, ok


class StaffRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StaffRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return ok(
            StaffProfileSerializer(user).data,
            "Staff account created.",
            status.HTTP_201_CREATED,
        )


class StaffLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StaffLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = StaffUser.objects.filter(email=email, is_active=True).first()
        if not user or not user.check_password(password):
            return fail(
                "Invalid credentials.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        token_payload = issue_staff_token(user, settings.SERVICE_NAME)
        return ok(token_payload, "Login successful.")


class StaffProfileAPIView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        user = StaffUser.objects.filter(id=request.user.id, is_active=True).first()
        if not user:
            return fail(
                "Staff user not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ok(StaffProfileSerializer(user).data, "Profile loaded.")
