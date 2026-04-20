from django.urls import include, path

urlpatterns = [
    path("api/customers/", include("apps.customers.urls")),
    path("api/", include("apps.cart.urls")),
]
