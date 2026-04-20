from rest_framework import status
from rest_framework.views import APIView

from apps.cart.models import Order
from apps.cart.serializers import (
    CartItemUpdateSerializer,
    CartItemWriteSerializer,
    CartSerializer,
    OrderSerializer,
)
from apps.cart.services import CartService, CheckoutError
from apps.customers.models import Customer
from shared.common.permissions import IsCustomerUser
from shared.common.responses import fail, ok


class CustomerScopedAPIView(APIView):
    permission_classes = [IsCustomerUser]

    def get_customer(self, request):
        return Customer.objects.filter(id=request.user.id, is_active=True).first()

    def get_cart_service(self):
        return CartService()


class CartDetailAPIView(CustomerScopedAPIView):
    def get(self, request):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        cart = self.get_cart_service().get_or_create_active_cart(customer)
        return ok(CartSerializer(cart).data, "Cart loaded.")


class CartItemCreateAPIView(CustomerScopedAPIView):
    def post(self, request):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart = self.get_cart_service().add_item(customer, **serializer.validated_data)
        except CheckoutError as exc:
            return fail(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return ok(CartSerializer(cart).data, "Item added to cart.", status.HTTP_201_CREATED)


class CartItemUpdateDeleteAPIView(CustomerScopedAPIView):
    def put(self, request, item_id):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart = self.get_cart_service().update_item(
                customer,
                item_id,
                serializer.validated_data["quantity"],
            )
        except CheckoutError as exc:
            return fail(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return ok(CartSerializer(cart).data, "Cart item updated.")

    def delete(self, request, item_id):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        try:
            cart = self.get_cart_service().remove_item(customer, item_id)
        except CheckoutError as exc:
            return fail(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        return ok(CartSerializer(cart).data, "Cart item removed.")


class CartClearAPIView(CustomerScopedAPIView):
    def delete(self, request):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        cart = self.get_cart_service().clear_cart(customer)
        return ok(CartSerializer(cart).data, "Cart cleared.")


class CheckoutAPIView(CustomerScopedAPIView):
    def post(self, request):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        try:
            order = self.get_cart_service().checkout(customer)
        except CheckoutError as exc:
            return fail(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        return ok(OrderSerializer(order).data, "Checkout completed successfully.")


class OrderListAPIView(CustomerScopedAPIView):
    def get(self, request):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        orders = Order.objects.filter(customer=customer)
        return ok(OrderSerializer(orders, many=True).data, "Orders loaded.")


class OrderDetailAPIView(CustomerScopedAPIView):
    def get(self, request, order_id):
        customer = self.get_customer(request)
        if not customer:
            return fail("Customer not found.", status_code=status.HTTP_404_NOT_FOUND)
        order = Order.objects.filter(customer=customer, id=order_id).first()
        if not order:
            return fail("Order not found.", status_code=status.HTTP_404_NOT_FOUND)
        return ok(OrderSerializer(order).data, "Order loaded.")
