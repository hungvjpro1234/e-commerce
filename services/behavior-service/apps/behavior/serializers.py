from rest_framework import serializers

from apps.behavior.models import BehaviorEvent


class BehaviorEventWriteSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=[choice[0] for choice in BehaviorEvent.EVENT_CHOICES])
    product_id = serializers.UUIDField()
    product_service = serializers.CharField(max_length=32)
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    page_context = serializers.CharField(max_length=64, required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class BehaviorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorEvent
        fields = ["id", "user_id", "product_id", "product_service", "event_type", "quantity", "metadata", "created_at"]
