from rest_framework import serializers

from apps.products.models import LaptopCategory, LaptopProduct


class LaptopCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LaptopCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class LaptopProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=LaptopCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LaptopProduct
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
            "cpu",
            "ram_gb",
            "storage_gb",
            "display_size",

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
