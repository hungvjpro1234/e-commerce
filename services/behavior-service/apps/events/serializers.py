import csv

from rest_framework import serializers

from apps.events.models import BehaviorEvent


PRODUCT_REQUIRED_EVENT_TYPES = {
    BehaviorEvent.EventType.VIEW_PRODUCT,
    BehaviorEvent.EventType.ADD_TO_CART,
    BehaviorEvent.EventType.UPDATE_CART_QUANTITY,
    BehaviorEvent.EventType.REMOVE_FROM_CART,
    BehaviorEvent.EventType.PURCHASE,
}

QUANTITY_REQUIRED_EVENT_TYPES = {
    BehaviorEvent.EventType.ADD_TO_CART,
    BehaviorEvent.EventType.UPDATE_CART_QUANTITY,
    BehaviorEvent.EventType.PURCHASE,
}


class BehaviorEventIngestSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField(required=False)
    occurred_at = serializers.DateTimeField(required=False)

    class Meta:
        model = BehaviorEvent
        fields = [
            "id",
            "user_id",
            "session_id",
            "event_type",
            "product_service",
            "product_id",
            "category",
            "search_keyword",
            "quantity",
            "occurred_at",
            "metadata",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        event_type = attrs.get("event_type")
        product_service = attrs.get("product_service")
        product_id = attrs.get("product_id")
        search_keyword = attrs.get("search_keyword", "")
        quantity = attrs.get("quantity")
        metadata = attrs.get("metadata", {})

        if metadata is None or not isinstance(metadata, dict):
            raise serializers.ValidationError({"metadata": "metadata must be an object."})

        if event_type in PRODUCT_REQUIRED_EVENT_TYPES:
            if not product_service:
                raise serializers.ValidationError(
                    {"product_service": "This field is required for the selected event_type."}
                )
            if not product_id:
                raise serializers.ValidationError(
                    {"product_id": "This field is required for the selected event_type."}
                )

        if event_type == BehaviorEvent.EventType.SEARCH and not str(search_keyword).strip():
            raise serializers.ValidationError(
                {"search_keyword": "search_keyword is required for search events."}
            )

        if event_type in QUANTITY_REQUIRED_EVENT_TYPES and quantity is None:
            raise serializers.ValidationError(
                {"quantity": "quantity is required for the selected event_type."}
            )

        if quantity is not None and quantity < 1:
            raise serializers.ValidationError({"quantity": "quantity must be greater than 0."})

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data.setdefault("metadata", {})
        validated_data["source_service"] = request.headers.get("X-Service-Name", "unknown-service")
        return super().create(validated_data)


class BehaviorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorEvent
        fields = [
            "id",
            "user_id",
            "session_id",
            "source_service",
            "event_type",
            "product_service",
            "product_id",
            "category",
            "search_keyword",
            "quantity",
            "occurred_at",
            "metadata",
            "created_at",
            "updated_at",
        ]


CSV_EXPORT_FIELDS = [
    "id",
    "user_id",
    "session_id",
    "source_service",
    "event_type",
    "product_service",
    "product_id",
    "category",
    "search_keyword",
    "quantity",
    "occurred_at",
    "metadata",
    "created_at",
]


def write_events_csv(response, events):
    writer = csv.DictWriter(response, fieldnames=CSV_EXPORT_FIELDS)
    writer.writeheader()
    for event in events:
        writer.writerow(
            {
                "id": str(event.id),
                "user_id": str(event.user_id),
                "session_id": event.session_id,
                "source_service": event.source_service,
                "event_type": event.event_type,
                "product_service": event.product_service,
                "product_id": str(event.product_id) if event.product_id else "",
                "category": event.category,
                "search_keyword": event.search_keyword,
                "quantity": event.quantity if event.quantity is not None else "",
                "occurred_at": event.occurred_at.isoformat(),
                "metadata": event.metadata,
                "created_at": event.created_at.isoformat(),
            }
        )
