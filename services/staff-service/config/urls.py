from django.urls import include, path

urlpatterns = [
    path("api/staff/", include("apps.staff_accounts.urls")),
]
