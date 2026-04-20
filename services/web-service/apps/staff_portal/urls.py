from django.urls import path
from apps.staff_portal import views

urlpatterns = [
    path("login", views.StaffLoginView.as_view(), name="staff_login"),
    path("logout", views.StaffLogoutView.as_view(), name="staff_logout"),
    path("dashboard", views.DashboardView.as_view(), name="staff_dashboard"),
    path("products/<str:domain>", views.ProductListView.as_view(), name="staff_products"),
    path("products/<str:domain>/new", views.ProductCreateView.as_view(), name="staff_product_create"),
    path("products/<str:domain>/<str:product_id>/edit", views.ProductEditView.as_view(), name="staff_product_edit"),
    path("products/<str:domain>/<str:product_id>/delete", views.ProductDeleteView.as_view(), name="staff_product_delete"),
]
