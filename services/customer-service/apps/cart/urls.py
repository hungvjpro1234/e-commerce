from django.urls import path

from apps.cart.views import (
    CartClearAPIView,
    CartDetailAPIView,
    CartItemCreateAPIView,
    CartItemUpdateDeleteAPIView,
    CheckoutAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
)

urlpatterns = [
    path("cart", CartDetailAPIView.as_view()),
    path("cart/items", CartItemCreateAPIView.as_view()),
    path("cart/items/<uuid:item_id>", CartItemUpdateDeleteAPIView.as_view()),
    path("cart/clear", CartClearAPIView.as_view()),
    path("checkout", CheckoutAPIView.as_view()),
    path("orders", OrderListAPIView.as_view()),
    path("orders/<uuid:order_id>", OrderDetailAPIView.as_view()),
]
