from rest_framework import serializers

from apps.products.models import GamingCategory, GamingProduct


class GamingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GamingCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class GamingProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=GamingCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = GamingProduct
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image_url",
            "is_active",

            "brand",
            "platform",
            "connectivity",
            "rgb_support",
            "warranty_months",

            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductValidationSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class StockDecrementSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
