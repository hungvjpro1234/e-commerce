from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.customers.models import Customer
from apps.customers.serializers import (
    CustomerLoginSerializer,
    CustomerProfileSerializer,
    CustomerRegisterSerializer,
)
from apps.customers.services import issue_customer_token
from shared.common.permissions import IsCustomerUser
from shared.common.responses import fail, ok


class CustomerRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return ok(
            CustomerProfileSerializer(customer).data,
            "Customer account created.",
            status.HTTP_201_CREATED,
        )


class CustomerLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        customer = Customer.objects.filter(email=email, is_active=True).first()
        if not customer or not customer.check_password(password):
            return fail(
                "Invalid credentials.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        token_payload = issue_customer_token(customer, settings.SERVICE_NAME)
        return ok(token_payload, "Login successful.")


class CustomerProfileAPIView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request):
        customer = Customer.objects.filter(id=request.user.id, is_active=True).first()
        if not customer:
            return fail(
                "Customer not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ok(CustomerProfileSerializer(customer).data, "Profile loaded.")
