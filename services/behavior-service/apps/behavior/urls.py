from django.urls import path

from apps.behavior.views import BehaviorEventCreateAPIView, InternalBehaviorEventCreateAPIView, TrainingDataAPIView

urlpatterns = [
    path("events", BehaviorEventCreateAPIView.as_view()),
    path("internal/events", InternalBehaviorEventCreateAPIView.as_view()),
    path("internal/training-data", TrainingDataAPIView.as_view()),
]
