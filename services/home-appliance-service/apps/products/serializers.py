from rest_framework import serializers

from apps.products.models import HomeApplianceCategory, HomeApplianceProduct


class HomeApplianceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeApplianceCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class HomeApplianceProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=HomeApplianceCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = HomeApplianceProduct
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
            "power_watt",
            "capacity",
            "energy_rating",
            "appliance_type",

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
