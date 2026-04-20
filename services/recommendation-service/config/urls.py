from django.urls import include, path

urlpatterns = [
    path("api/recommend/", include("apps.recommendations.urls")),
]
