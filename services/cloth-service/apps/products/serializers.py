from rest_framework import serializers

from apps.products.models import ClothCategory, ClothProduct


class ClothCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class ClothProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=ClothCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ClothProduct
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image_url",
            "is_active",

            "size",
            "material",
            "color",
            "gender",

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
