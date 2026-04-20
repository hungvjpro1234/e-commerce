from django.views.generic import TemplateView

from apps.gateway.clients import ApiError, ProductGateway, RecommendationGateway


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["featured_products"] = ProductGateway().list_all()[:9]
        except (ApiError, Exception):
            context["featured_products"] = []
        context["recommended_products"] = []
        token = self.request.session.get("customer_access_token")
        if token:
            try:
                recommendation_resp = RecommendationGateway().recommendations(token, limit=6)
                context["recommended_products"] = recommendation_resp.get("data", {}).get("items", [])
            except (ApiError, Exception):
                context["recommended_products"] = []
        return context
