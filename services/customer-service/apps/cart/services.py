import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.behavior_tracking import emit_behavior_event
from apps.cart.models import Cart, CartItem, Order, OrderItem
from shared.common.product_client import ProductServiceClient


class CheckoutError(Exception):
    pass


class CartService:
    def __init__(self):
        self.client = ProductServiceClient(settings.INTERNAL_SERVICE_TOKEN)

    def get_or_create_active_cart(self, customer):
        cart, _ = Cart.objects.get_or_create(customer=customer, status=Cart.Status.ACTIVE)
        return cart

    def add_item(self, customer, product_service, product_id, quantity):
        validation = self.client.validate_product(product_service, str(product_id), quantity)
        if not validation.get("exists"):
            raise CheckoutError("Product does not exist.")
        if not validation.get("sufficient_stock"):
            raise CheckoutError("Not enough stock for the requested quantity.")

        product = validation["product"]
        cart = self.get_or_create_active_cart(customer)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_service=product_service,
            product_id=product_id,
            defaults={
                "product_name_snapshot": product["name"],
                "unit_price_snapshot": product["price"],
                "quantity": quantity,
                "image_url_snapshot": product.get("image_url", ""),
            },
        )
        if not created:
            item.quantity = quantity
            item.product_name_snapshot = product["name"]
            item.unit_price_snapshot = product["price"]
            item.image_url_snapshot = product.get("image_url", "")
            item.save(
                update_fields=[
                    "quantity",
                    "product_name_snapshot",
                    "unit_price_snapshot",
                    "image_url_snapshot",
                    "updated_at",
                ]
            )
        emit_behavior_event(
            user_id=customer.id,
            event_type="add_to_cart",
            product_service=product_service,
            product_id=product_id,
            category=product_service,
            quantity=quantity,
            metadata={"source": "customer-service"},
        )
        return self.get_or_create_active_cart(customer)

    def update_item(self, customer, item_id, quantity):
        cart = self.get_or_create_active_cart(customer)
        item = cart.items.filter(id=item_id).first()
        if not item:
            raise CheckoutError("Cart item not found.")
        validation = self.client.validate_product(item.product_service, str(item.product_id), quantity)
        if not validation.get("exists"):
            raise CheckoutError("Product no longer exists.")
        if not validation.get("sufficient_stock"):
            raise CheckoutError("Not enough stock for the requested quantity.")
        product = validation["product"]
        item.quantity = quantity
        item.product_name_snapshot = product["name"]
        item.unit_price_snapshot = product["price"]
        item.image_url_snapshot = product.get("image_url", "")
        item.save(
            update_fields=[
                "quantity",
                "product_name_snapshot",
                "unit_price_snapshot",
                "image_url_snapshot",
                "updated_at",
            ]
        )
        emit_behavior_event(
            user_id=customer.id,
            event_type="update_cart_quantity",
            product_service=item.product_service,
            product_id=item.product_id,
            category=item.product_service,
            quantity=quantity,
            metadata={"source": "customer-service"},
        )
        return self.get_or_create_active_cart(customer)

    def remove_item(self, customer, item_id):
        cart = self.get_or_create_active_cart(customer)
        item = cart.items.filter(id=item_id).first()
        if not item:
            raise CheckoutError("Cart item not found.")
        emit_behavior_event(
            user_id=customer.id,
            event_type="remove_from_cart",
            product_service=item.product_service,
            product_id=item.product_id,
            category=item.product_service,
            quantity=item.quantity,
            metadata={"source": "customer-service"},
        )
        item.delete()
        return self.get_or_create_active_cart(customer)

    def clear_cart(self, customer):
        cart = self.get_or_create_active_cart(customer)
        cart.items.all().delete()
        return cart

    def checkout(self, customer):
        cart = self.get_or_create_active_cart(customer)
        items = list(cart.items.all())
        if not items:
            raise CheckoutError("Cart is empty.")

        validated_items = []
        for item in items:
            validation = self.client.validate_product(
                item.product_service,
                str(item.product_id),
                item.quantity,
            )
            if not validation.get("exists"):
                raise CheckoutError(f"Product {item.product_id} no longer exists.")
            if not validation.get("sufficient_stock"):
                raise CheckoutError(f"Insufficient stock for {item.product_name_snapshot}.")
            validated_items.append((item, validation["product"]))

        for item, _product in validated_items:
            self.client.decrement_stock(item.product_service, str(item.product_id), item.quantity)

        with transaction.atomic():
            order = Order.objects.create(
                customer=customer,
                status=Order.Status.PAID,
                payment_reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
            )
            total_amount = Decimal("0.00")
            for item, product in validated_items:
                unit_price = Decimal(str(product["price"]))
                line_total = unit_price * item.quantity
                total_amount += line_total
                OrderItem.objects.create(
                    order=order,
                    product_service=item.product_service,
                    product_id=item.product_id,
                    product_name=product["name"],
                    unit_price=unit_price,
                    quantity=item.quantity,
                    line_total=line_total,
                    image_url=product.get("image_url", ""),
                )
            order.total_amount = total_amount
            order.save(update_fields=["total_amount", "updated_at"])
            cart.status = Cart.Status.CHECKED_OUT
            cart.checked_out_at = timezone.now()
            cart.save(update_fields=["status", "checked_out_at", "updated_at"])
            cart.items.all().delete()
        for item, _product in validated_items:
            emit_behavior_event(
                user_id=customer.id,
                event_type="purchase",
                product_service=item.product_service,
                product_id=item.product_id,
                category=item.product_service,
                quantity=item.quantity,
                metadata={"order_id": str(order.id), "payment_reference": order.payment_reference},
            )
        return order
