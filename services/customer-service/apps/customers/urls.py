from django.urls import path

from apps.customers.views import (
    CustomerLoginAPIView,
    CustomerProfileAPIView,
    CustomerRegisterAPIView,
)

urlpatterns = [
    path("register", CustomerRegisterAPIView.as_view()),
    path("login", CustomerLoginAPIView.as_view()),
    path("profile", CustomerProfileAPIView.as_view()),
]
