from rest_framework import serializers

from shared.common.product_domains import PRODUCT_SERVICE_CHOICES

BEHAVIOR_CHOICES = (
    ("register", "register"),
    ("login", "login"),
    ("search", "search"),
    ("view_product", "view_product"),
    ("add_to_cart", "add_to_cart"),
    ("update_cart_quantity", "update_cart_quantity"),
    ("remove_from_cart", "remove_from_cart"),
    ("purchase", "purchase"),
)


class BehaviorContextSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=BEHAVIOR_CHOICES)
    category = serializers.CharField(required=False, allow_blank=True, default="")
    product_service = serializers.ChoiceField(
        choices=PRODUCT_SERVICE_CHOICES,
        required=False,
        allow_blank=True,
        default="",
    )
    product_id = serializers.CharField(required=False, allow_blank=True, default="")
    source_service = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.IntegerField(required=False, min_value=0, default=0)


class PredictNextBehaviorRequestSerializer(serializers.Serializer):
    recent_events = BehaviorContextSerializer(many=True, min_length=1)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=8, default=3)


class RecommendProductsRequestSerializer(PredictNextBehaviorRequestSerializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
    search_keyword = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(required=False, allow_blank=True, default="")
    product_service = serializers.ChoiceField(
        choices=PRODUCT_SERVICE_CHOICES,
        required=False,
        allow_blank=True,
        default="",
    )
    product_id = serializers.CharField(required=False, allow_blank=True, default="")
