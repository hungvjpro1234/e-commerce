from rest_framework import serializers

from apps.products.models import SportsCategory, SportsProduct


class SportsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SportsCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class SportsProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=SportsCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SportsProduct
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
            "sport_type",
            "material",
            "size",
            "target_gender",

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
