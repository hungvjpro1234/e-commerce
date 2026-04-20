from django.urls import path

from apps.staff_accounts.views import (
    StaffLoginAPIView,
    StaffProfileAPIView,
    StaffRegisterAPIView,
)

urlpatterns = [
    path("register", StaffRegisterAPIView.as_view()),
    path("login", StaffLoginAPIView.as_view()),
    path("profile", StaffProfileAPIView.as_view()),
]
