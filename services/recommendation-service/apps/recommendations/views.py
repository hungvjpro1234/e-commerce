from rest_framework.views import APIView

from apps.recommendations.services import RecommendationEngine
from shared.common.permissions import IsCustomerUser
from shared.common.responses import ok


class RecommendationListAPIView(APIView):
    permission_classes = [IsCustomerUser]

    def get(self, request):
        limit = int(request.query_params.get("limit", 6))
        domain = request.query_params.get("domain", "")
        product_id = request.query_params.get("product_id", "")
        payload = RecommendationEngine().recommend(user_id=str(request.user.id), limit=limit, domain=domain, product_id=product_id)
        return ok(payload, "Recommendations loaded.")
