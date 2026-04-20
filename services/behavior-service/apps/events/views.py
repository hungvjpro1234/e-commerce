from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from apps.events.models import BehaviorEvent
from apps.events.serializers import (
    BehaviorEventIngestSerializer,
    BehaviorEventSerializer,
    write_events_csv,
)
from shared.common.permissions import IsInternalService
from shared.common.responses import ok


class BehaviorEventIngestAPIView(APIView):
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = BehaviorEventIngestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return ok(
            {
                "id": str(event.id),
                "event_type": event.event_type,
            },
            "Behavior event stored.",
            status.HTTP_201_CREATED,
        )


class BehaviorEventListAPIView(APIView):
    permission_classes = [IsInternalService]

    def get(self, request):
        events = BehaviorEvent.objects.all()

        user_id = request.query_params.get("user_id")
        if user_id:
            events = events.filter(user_id=user_id)

        event_type = request.query_params.get("event_type")
        if event_type:
            events = events.filter(event_type=event_type)

        source_service = request.query_params.get("source_service")
        if source_service:
            events = events.filter(source_service=source_service)

        limit = request.query_params.get("limit")
        if limit:
            try:
                events = events[: max(1, min(int(limit), 500))]
            except ValueError:
                events = events[:100]
        else:
            events = events[:100]

        return ok(BehaviorEventSerializer(events, many=True).data, "Behavior events loaded.")


class BehaviorEventExportAPIView(APIView):
    permission_classes = [IsInternalService]

    def get(self, request):
        events = BehaviorEvent.objects.all()

        user_id = request.query_params.get("user_id")
        if user_id:
            events = events.filter(user_id=user_id)

        event_type = request.query_params.get("event_type")
        if event_type:
            events = events.filter(event_type=event_type)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="behavior-events.csv"'
        write_events_csv(response, events)
        return response
