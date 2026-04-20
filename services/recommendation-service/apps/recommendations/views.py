from rest_framework.views import APIView

from apps.recommendations.serializers import (
    PredictNextBehaviorRequestSerializer,
    RecommendProductsRequestSerializer,
)
from apps.recommendations.services import get_recommendation_service
from shared.common.responses import ok


class PredictNextBehaviorAPIView(APIView):
    def post(self, request):
        serializer = PredictNextBehaviorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = get_recommendation_service()
        result = service.predict_next_behavior(
            serializer.validated_data["recent_events"],
            top_k=serializer.validated_data["top_k"],
        )
        return ok(result, "Next behavior predicted.")


class RecommendProductsAPIView(APIView):
    def post(self, request):
        serializer = RecommendProductsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        service = get_recommendation_service()
        result = service.recommend_products(
            recent_events=payload["recent_events"],
            top_k=payload["limit"],
            search_keyword=payload.get("search_keyword", ""),
            category=payload.get("category", ""),
            product_service=payload.get("product_service", ""),
            product_id=payload.get("product_id", ""),
        )
        return ok(result, "Product recommendations loaded.")
