from django.views.generic import TemplateView

from apps.gateway.clients import ApiError, ProductGateway


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["featured_products"] = ProductGateway().list_all()[:9]
        except (ApiError, Exception):
            context["featured_products"] = []
        return context
