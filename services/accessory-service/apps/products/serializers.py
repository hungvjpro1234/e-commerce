from rest_framework import serializers

from apps.products.models import AccessoryCategory, AccessoryProduct


class AccessoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessoryCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class AccessoryProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=AccessoryCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AccessoryProduct
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
            "accessory_type",
            "compatibility",
            "wireless",
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
