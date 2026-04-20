from rest_framework import serializers

from apps.products.models import MobileCategory, MobileProduct


class MobileCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class MobileProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=MobileCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MobileProduct
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
            "operating_system",
            "screen_size",
            "battery_mah",
            "camera_mp",

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
