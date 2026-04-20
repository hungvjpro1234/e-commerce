from rest_framework import status
from rest_framework.views import APIView

from apps.behavior.models import UserItemAggregate
from apps.behavior.serializers import BehaviorEventSerializer, BehaviorEventWriteSerializer
from apps.behavior.services import BehaviorTracker
from shared.common.permissions import IsCustomerUser, IsInternalService
from shared.common.responses import fail, ok


class BehaviorEventCreateAPIView(APIView):
    permission_classes = [IsCustomerUser]

    def post(self, request):
        serializer = BehaviorEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        metadata = dict(payload.get("metadata") or {})
        if payload.get("page_context"):
            metadata["page_context"] = payload["page_context"]
        event = BehaviorTracker().track_event(
            user_id=request.user.id,
            product_id=payload["product_id"],
            product_service=payload["product_service"],
            event_type=payload["event_type"],
            quantity=payload.get("quantity", 1),
            metadata=metadata,
        )
        return ok(BehaviorEventSerializer(event).data, "Behavior event tracked.", status.HTTP_201_CREATED)


class InternalBehaviorEventCreateAPIView(APIView):
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = BehaviorEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.data.get("user_id")
        if not user_id:
            return fail("user_id is required.")
        payload = serializer.validated_data
        metadata = dict(payload.get("metadata") or {})
        if payload.get("page_context"):
            metadata["page_context"] = payload["page_context"]
        event = BehaviorTracker().track_event(
            user_id=user_id,
            product_id=payload["product_id"],
            product_service=payload["product_service"],
            event_type=payload["event_type"],
            quantity=payload.get("quantity", 1),
            metadata=metadata,
        )
        return ok(BehaviorEventSerializer(event).data, "Behavior event tracked.", status.HTTP_201_CREATED)


class TrainingDataAPIView(APIView):
    permission_classes = [IsInternalService]

    def get(self, request):
        rows = []
        for aggregate in UserItemAggregate.objects.all().order_by("user_id"):
            score = aggregate.view_count + (aggregate.cart_add_count * 3) + (aggregate.purchase_count * 5)
            rows.append({
                "user_id": str(aggregate.user_id),
                "product_id": str(aggregate.product_id),
                "product_service": aggregate.product_service,
                "item_key": f"{aggregate.product_service}::{aggregate.product_id}",
                "score": float(score),
            })
        return ok(rows, "Training data loaded.")
