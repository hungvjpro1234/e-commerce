from django.urls import path

from apps.events.views import (
    BehaviorEventExportAPIView,
    BehaviorEventIngestAPIView,
    BehaviorEventListAPIView,
)

urlpatterns = [
    path("internal/events", BehaviorEventIngestAPIView.as_view()),
    path("events", BehaviorEventListAPIView.as_view()),
    path("events/export", BehaviorEventExportAPIView.as_view()),
]
