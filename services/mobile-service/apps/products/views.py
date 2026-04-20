from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import MobileProduct
from apps.products.serializers import (
    MobileProductSerializer,
    ProductValidationSerializer,
    StockDecrementSerializer,
)
from apps.products.services import ProductDomainService
from shared.common.permissions import IsInternalService, IsStaffUser


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = MobileProductSerializer
    queryset = MobileProduct.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "retrieve"]:
            return queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsStaffUser()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class InternalValidateProductAPIView(APIView):
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = ProductValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductDomainService.get_active_product(
            serializer.validated_data["product_id"]
        )
        if not product:
            return Response(
                {
                    "exists": False,
                    "sufficient_stock": False,
                    "product": None,
                }
            )
        return Response(
            {
                "exists": True,
                "sufficient_stock": ProductDomainService.validate_stock(
                    product,
                    serializer.validated_data["quantity"],
                ),
                "product": MobileProductSerializer(product).data,
            }
        )


class InternalDecrementStockAPIView(APIView):
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = StockDecrementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductDomainService.get_active_product(
            serializer.validated_data["product_id"]
        )
        if not product:
            return Response(
                {"message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not ProductDomainService.validate_stock(
            product,
            serializer.validated_data["quantity"],
        ):
            return Response(
                {"message": "Not enough stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ProductDomainService.decrement_stock(
            product,
            serializer.validated_data["quantity"],
        )
        return Response(
            {
                "message": "Stock updated.",
                "product": MobileProductSerializer(product).data,
            }
        )
