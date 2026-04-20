from rest_framework import serializers

from apps.products.models import BeautyCategory, BeautyProduct


class BeautyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BeautyCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class BeautyProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=BeautyCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = BeautyProduct
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
            "skin_type",
            "volume_ml",
            "expiry_months",
            "origin_country",

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
