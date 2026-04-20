from django.urls import path

from apps.recommendations.views import (
    PredictNextBehaviorAPIView,
    RecommendProductsAPIView,
)

urlpatterns = [
    path("predict-next-behavior", PredictNextBehaviorAPIView.as_view()),
    path("products", RecommendProductsAPIView.as_view()),
]
