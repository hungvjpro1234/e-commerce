from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.products.views import (
    InternalDecrementStockAPIView,
    InternalValidateProductAPIView,
    ProductViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r"food-products", ProductViewSet, basename="food-products")

urlpatterns = [
    path("", include(router.urls)),
    path("internal/products/validate", InternalValidateProductAPIView.as_view()),
    path("internal/products/decrement-stock", InternalDecrementStockAPIView.as_view()),
]
