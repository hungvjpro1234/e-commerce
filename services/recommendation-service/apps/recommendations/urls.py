from django.urls import path

from apps.recommendations.views import RecommendationListAPIView

urlpatterns = [
    path("recommendations/me", RecommendationListAPIView.as_view()),
]
