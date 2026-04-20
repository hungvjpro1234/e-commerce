from rest_framework import serializers

from apps.products.models import FoodCategory, FoodProduct


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class FoodProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=FoodCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = FoodProduct
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
            "weight_g",
            "flavor",
            "expiry_date",
            "is_organic",

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
