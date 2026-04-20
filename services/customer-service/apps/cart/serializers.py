from decimal import Decimal

from rest_framework import serializers

from apps.cart.models import Cart, CartItem, Order, OrderItem


class CartItemWriteSerializer(serializers.Serializer):
    product_service = serializers.ChoiceField(choices=CartItem.ProductService.choices)
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_service",
            "product_id",
            "product_name_snapshot",
            "unit_price_snapshot",
            "quantity",
            "image_url_snapshot",
            "subtotal",
            "created_at",
            "updated_at",
        ]

    def get_subtotal(self, obj):
        return Decimal(obj.unit_price_snapshot) * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "status", "items", "total_amount", "created_at", "updated_at"]

    def get_total_amount(self, obj):
        return sum(
            (item.unit_price_snapshot * item.quantity for item in obj.items.all()),
            Decimal("0.00"),
        )


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_service",
            "product_id",
            "product_name",
            "unit_price",
            "quantity",
            "line_total",
            "image_url",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "total_amount", "payment_reference", "items", "created_at", "updated_at"]
