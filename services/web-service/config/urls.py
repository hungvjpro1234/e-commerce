from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.customer_portal.urls")),
    path("staff/", include("apps.staff_portal.urls")),
]
