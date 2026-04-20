from django.urls import path
from apps.customer_portal import views

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("profile", views.ProfileView.as_view(), name="profile"),
    path("products", views.ProductListView.as_view(), name="products"),
    path("products/<str:domain>/<str:product_id>", views.ProductDetailView.as_view(), name="product_detail"),
    path("cart", views.CartView.as_view(), name="cart"),
    path("cart/add", views.CartAddView.as_view(), name="cart_add"),
    path("cart/update/<str:item_id>", views.CartUpdateView.as_view(), name="cart_update"),
    path("cart/remove/<str:item_id>", views.CartRemoveView.as_view(), name="cart_remove"),
    path("cart/clear", views.CartClearView.as_view(), name="cart_clear"),
    path("checkout", views.CheckoutView.as_view(), name="checkout"),
    path("orders", views.OrderListView.as_view(), name="orders"),
    path("orders/<str:order_id>", views.OrderDetailView.as_view(), name="order_detail"),
]
