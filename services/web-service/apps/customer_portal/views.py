import json

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from apps.gateway.behavior import emit_behavior_event
from apps.gateway.clients import (
    ApiError,
    ChatbotGateway,
    CustomerGateway,
    ProductGateway,
    RecommendationGateway,
)

customer_gw = CustomerGateway()
product_gw = ProductGateway()
recommendation_gw = RecommendationGateway()
chatbot_gw = ChatbotGateway()
RECENT_EVENTS_SESSION_KEY = "customer_recent_behavior_events"
RECENT_EVENTS_LIMIT = 6


def get_customer_tracking_context(request):
    profile = request.session.get("customer_profile") or {}
    user_id = profile.get("id")
    if not user_id:
        return None
    return {
        "user_id": user_id,
        "session_id": request.session.session_key or "",
    }


def get_recent_behavior_events(request):
    return list(request.session.get(RECENT_EVENTS_SESSION_KEY, []))


def push_recent_behavior_event(
    request,
    *,
    event_type,
    category="",
    product_service="",
    product_id="",
    quantity=0,
    source_service="web-service",
):
    recent_events = get_recent_behavior_events(request)
    recent_events.append(
        {
            "event_type": event_type,
            "category": category or "",
            "product_service": product_service or "",
            "product_id": str(product_id or ""),
            "quantity": int(quantity or 0),
            "source_service": source_service,
        }
    )
    request.session[RECENT_EVENTS_SESSION_KEY] = recent_events[-RECENT_EVENTS_LIMIT:]
    request.session.modified = True


def get_recommendation_payload(request, *, cart_items=None):
    recent_events = get_recent_behavior_events(request)
    if recent_events:
        return recent_events
    if not cart_items:
        return []
    fallback_events = []
    for item in cart_items[-RECENT_EVENTS_LIMIT:]:
        fallback_events.append(
            {
                "event_type": "add_to_cart",
                "category": item.get("product_service", ""),
                "product_service": item.get("product_service", ""),
                "product_id": str(item.get("product_id", "")),
                "quantity": int(item.get("quantity", 0) or 0),
                "source_service": "web-service",
            }
        )
    return fallback_events


def load_recommendations(
    request,
    *,
    recent_events,
    search_keyword="",
    category="",
    product_service="",
    product_id="",
    limit=4,
):
    if not recent_events:
        return None
    try:
        return recommendation_gw.recommend_products(
            {
                "recent_events": recent_events,
                "search_keyword": search_keyword,
                "category": category,
                "product_service": product_service,
                "product_id": str(product_id or ""),
                "limit": limit,
            }
        )
    except ApiError:
        return None


def get_page_chat_context(*, domain="", product_id="", page_context="global_widget", cart_product_ids=None):
    return {
        "domain": domain or "",
        "product_id": str(product_id or ""),
        "page_context": page_context,
        "cart_product_ids": list(cart_product_ids or []),
    }


DOMAIN_LABELS = {
    "cloth": "Cloth",
    "laptop": "Laptop",
    "mobile": "Mobile",
    "accessory": "Tech Accessories",
    "home-appliance": "Home Appliances",
    "book": "Books",
    "beauty": "Beauty",
    "food": "Food & Drinks",
    "sports": "Sports",
    "gaming": "Gaming",
}

DOMAIN_ORDER = tuple(DOMAIN_LABELS.keys())

PRODUCT_DETAIL_FIELDS = {
    "cloth": [
        {"name": "size", "label": "Size"},
        {"name": "material", "label": "Material"},
        {"name": "color", "label": "Color"},
        {"name": "gender", "label": "Gender"},
    ],
    "laptop": [
        {"name": "brand", "label": "Brand"},
        {"name": "cpu", "label": "CPU"},
        {"name": "ram_gb", "label": "RAM", "suffix": " GB"},
        {"name": "storage_gb", "label": "Storage", "suffix": " GB"},
        {"name": "display_size", "label": "Display", "suffix": '"'},
    ],
    "mobile": [
        {"name": "brand", "label": "Brand"},
        {"name": "operating_system", "label": "OS"},
        {"name": "screen_size", "label": "Screen", "suffix": '"'},
        {"name": "battery_mah", "label": "Battery", "suffix": " mAh"},
        {"name": "camera_mp", "label": "Camera", "suffix": " MP"},
    ],
    "accessory": [
        {"name": "brand", "label": "Brand"},
        {"name": "accessory_type", "label": "Type"},
        {"name": "compatibility", "label": "Compatibility"},
        {"name": "wireless", "label": "Wireless"},
        {"name": "warranty_months", "label": "Warranty", "suffix": " months"},
    ],
    "home-appliance": [
        {"name": "brand", "label": "Brand"},
        {"name": "power_watt", "label": "Power", "suffix": " W"},
        {"name": "capacity", "label": "Capacity"},
        {"name": "energy_rating", "label": "Energy Rating"},
        {"name": "appliance_type", "label": "Type"},
    ],
    "book": [
        {"name": "author", "label": "Author"},
        {"name": "publisher", "label": "Publisher"},
        {"name": "language", "label": "Language"},
        {"name": "page_count", "label": "Pages"},
        {"name": "genre", "label": "Genre"},
    ],
    "beauty": [
        {"name": "brand", "label": "Brand"},
        {"name": "skin_type", "label": "Skin Type"},
        {"name": "volume_ml", "label": "Volume", "suffix": " ml"},
        {"name": "expiry_months", "label": "Shelf Life", "suffix": " months"},
        {"name": "origin_country", "label": "Origin"},
    ],
    "food": [
        {"name": "brand", "label": "Brand"},
        {"name": "weight_g", "label": "Weight", "suffix": " g"},
        {"name": "flavor", "label": "Flavor"},
        {"name": "expiry_date", "label": "Expiry Date"},
        {"name": "is_organic", "label": "Organic"},
    ],
    "sports": [
        {"name": "brand", "label": "Brand"},
        {"name": "sport_type", "label": "Sport"},
        {"name": "material", "label": "Material"},
        {"name": "size", "label": "Size"},
        {"name": "target_gender", "label": "Target Gender"},
    ],
    "gaming": [
        {"name": "brand", "label": "Brand"},
        {"name": "platform", "label": "Platform"},
        {"name": "connectivity", "label": "Connectivity"},
        {"name": "rgb_support", "label": "RGB Support"},
        {"name": "warranty_months", "label": "Warranty", "suffix": " months"},
    ],
}


def require_customer(view_method):
    def wrapper(self, request, *args, **kwargs):
        if not request.session.get("customer_access_token"):
            messages.error(request, "Please log in first.")
            return redirect("/login")
        return view_method(self, request, *args, **kwargs)
    wrapper.__name__ = view_method.__name__
    return wrapper


class RegisterView(View):
    def get(self, request):
        if request.session.get("customer_access_token"):
            return redirect("/products")
        return render(request, "customer_portal/register.html")

    def post(self, request):
        payload = {
            "email": request.POST.get("email"),
            "full_name": request.POST.get("full_name"),
            "password": request.POST.get("password"),
        }
        try:
            customer_gw.register(payload)
            messages.success(request, "Account created! Please log in.")
            return redirect("/login")
        except ApiError as exc:
            messages.error(request, str(exc))
            return render(request, "customer_portal/register.html")


class LoginView(View):
    def get(self, request):
        if request.session.get("customer_access_token"):
            return redirect("/products")
        return render(request, "customer_portal/login.html")

    def post(self, request):
        try:
            resp = customer_gw.login({
                "email": request.POST.get("email"),
                "password": request.POST.get("password"),
            })
            data = resp.get("data", {})
            request.session["customer_access_token"] = data["access_token"]
            request.session["customer_profile"] = data["user"]
            messages.success(request, f"Welcome back, {data['user']['full_name']}!")
            return redirect("/products")
        except ApiError as exc:
            messages.error(request, str(exc))
            return render(request, "customer_portal/login.html")


class LogoutView(View):
    def get(self, request):
        request.session.pop("customer_access_token", None)
        request.session.pop("customer_profile", None)
        request.session.pop(RECENT_EVENTS_SESSION_KEY, None)
        messages.success(request, "Logged out.")
        return redirect("/")


class ProfileView(View):
    @require_customer
    def get(self, request):
        return render(request, "customer_portal/profile.html", {
            "profile": request.session.get("customer_profile"),
        })


class ProductListView(View):
    def get(self, request):
        domain_filter = request.GET.get("domain", "")
        search = request.GET.get("q", "").lower()
        recommendations = None
        try:
            if domain_filter and domain_filter in DOMAIN_LABELS:
                products = product_gw.list_by_domain(domain_filter)
            else:
                products = product_gw.list_all()
                domain_filter = ""
            if search:
                products = [p for p in products if search in p.get("name", "").lower()]
                tracking = get_customer_tracking_context(request)
                if tracking:
                    emit_behavior_event(
                        user_id=tracking["user_id"],
                        session_id=tracking["session_id"],
                        event_type="search",
                        category=domain_filter,
                        search_keyword=search,
                        metadata={
                            "source": "web-service",
                            "domain_filter": domain_filter,
                        },
                    )
                    push_recent_behavior_event(
                        request,
                        event_type="search",
                        category=domain_filter,
                        quantity=len(products),
                    )
                    recommendations = load_recommendations(
                        request,
                        recent_events=get_recent_behavior_events(request),
                        search_keyword=search,
                        category=domain_filter,
                        product_service=domain_filter,
                        limit=4,
                    )
        except ApiError:
            products = []
        return render(request, "customer_portal/products.html", {
            "products": products,
            "domain_filter": domain_filter,
            "search": search,
            "domain_labels": DOMAIN_LABELS,
            "domain_order": DOMAIN_ORDER,
            "recommendations": recommendations,
            "chat_context": get_page_chat_context(
                domain=domain_filter,
                page_context="product_listing_search" if search else "product_listing",
            ),
        })


class ProductDetailView(View):
    def get(self, request, domain, product_id):
        if domain not in DOMAIN_LABELS:
            messages.error(request, "Unknown product category.")
            return redirect("/products")
        try:
            product = product_gw.detail(domain, product_id)
        except ApiError as exc:
            messages.error(request, str(exc))
            return redirect("/products")
        tracking = get_customer_tracking_context(request)
        if tracking:
            emit_behavior_event(
                user_id=tracking["user_id"],
                session_id=tracking["session_id"],
                event_type="view_product",
                product_service=domain,
                product_id=product_id,
                category=domain,
                metadata={"source": "web-service"},
            )
            push_recent_behavior_event(
                request,
                event_type="view_product",
                category=domain,
                product_service=domain,
                product_id=product_id,
            )
        return render(request, "customer_portal/product_detail.html", {
            "product": product,
            "domain": domain,
            "detail_fields": PRODUCT_DETAIL_FIELDS.get(domain, []),
            "chat_context": get_page_chat_context(
                domain=domain,
                product_id=product_id,
                page_context="product_detail",
            ),
        })


class CartView(View):
    @require_customer
    def get(self, request):
        token = request.session["customer_access_token"]
        try:
            cart = customer_gw.cart(token)
            cart_data = cart.get("data", {})
        except ApiError:
            cart_data = {"items": [], "total_amount": "0.00"}
        cart_items = cart_data.get("items", [])
        cart_domain = cart_items[-1].get("product_service", "") if cart_items else ""
        recent_events = get_recommendation_payload(request, cart_items=cart_items)
        recommendations = load_recommendations(
            request,
            recent_events=recent_events,
            category=cart_domain,
            product_service=cart_domain,
            product_id=cart_items[-1].get("product_id", "") if cart_items else "",
            limit=4,
        )
        return render(
            request,
            "customer_portal/cart.html",
            {
                "cart": cart_data,
                "recommendations": recommendations,
                "chat_context": get_page_chat_context(
                    domain=cart_domain,
                    page_context="cart",
                    cart_product_ids=[str(item.get("product_id", "")) for item in cart_items if item.get("product_id")],
                ),
            },
        )


class CartAddView(View):
    @require_customer
    def post(self, request):
        token = request.session["customer_access_token"]
        try:
            product_service = request.POST.get("product_service")
            product_id = request.POST.get("product_id")
            quantity = int(request.POST.get("quantity", 1))
            customer_gw.add_cart_item(token, {
                "product_service": product_service,
                "product_id": product_id,
                "quantity": quantity,
            })
            push_recent_behavior_event(
                request,
                event_type="add_to_cart",
                category=product_service,
                product_service=product_service,
                product_id=product_id,
                quantity=quantity,
            )
            messages.success(request, "Item added to cart!")
        except ApiError as exc:
            messages.error(request, str(exc))
        return redirect(request.META.get("HTTP_REFERER", "/cart"))


class CartUpdateView(View):
    @require_customer
    def post(self, request, item_id):
        token = request.session["customer_access_token"]
        try:
            quantity = int(request.POST.get("quantity", 1))
            customer_gw.update_cart_item(token, item_id, {"quantity": quantity})
            push_recent_behavior_event(
                request,
                event_type="update_cart_quantity",
                quantity=quantity,
            )
        except ApiError as exc:
            messages.error(request, str(exc))
        return redirect("/cart")


class CartRemoveView(View):
    @require_customer
    def post(self, request, item_id):
        token = request.session["customer_access_token"]
        try:
            customer_gw.delete_cart_item(token, item_id)
            push_recent_behavior_event(request, event_type="remove_from_cart")
            messages.success(request, "Item removed.")
        except ApiError as exc:
            messages.error(request, str(exc))
        return redirect("/cart")


class CartClearView(View):
    @require_customer
    def post(self, request):
        token = request.session["customer_access_token"]
        try:
            customer_gw.clear_cart(token)
            messages.success(request, "Cart cleared.")
        except ApiError as exc:
            messages.error(request, str(exc))
        return redirect("/cart")


class CheckoutView(View):
    @require_customer
    def get(self, request):
        token = request.session["customer_access_token"]
        try:
            cart = customer_gw.cart(token)
            cart_data = cart.get("data", {})
        except ApiError:
            cart_data = {"items": [], "total_amount": "0.00"}
        return render(request, "customer_portal/checkout.html", {"cart": cart_data})

    @require_customer
    def post(self, request):
        token = request.session["customer_access_token"]
        try:
            result = customer_gw.checkout(token)
            order = result.get("data", {})
            push_recent_behavior_event(request, event_type="purchase")
            messages.success(request, f"Order #{order.get('payment_reference')} placed successfully!")
            return redirect(f"/orders/{order.get('id')}")
        except ApiError as exc:
            messages.error(request, str(exc))
            return redirect("/cart")


class OrderListView(View):
    @require_customer
    def get(self, request):
        token = request.session["customer_access_token"]
        try:
            resp = customer_gw.orders(token)
            orders = resp.get("data", [])
        except ApiError:
            orders = []
        return render(request, "customer_portal/orders.html", {"orders": orders})


class OrderDetailView(View):
    @require_customer
    def get(self, request, order_id):
        token = request.session["customer_access_token"]
        try:
            resp = customer_gw.order_detail(token, order_id)
            order = resp.get("data", {})
        except ApiError as exc:
            messages.error(request, str(exc))
            return redirect("/orders")
        return render(request, "customer_portal/order_detail.html", {"order": order})


class ChatContextProxyView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON payload."}, status=400)
        try:
            result = chatbot_gw.context(
                {
                    "message": payload.get("message", ""),
                    "context": payload.get("context", {}),
                }
            )
        except ApiError as exc:
            return JsonResponse({"message": str(exc)}, status=502)
        return JsonResponse({"data": result}, encoder=DjangoJSONEncoder)


class ChatMessageProxyView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON payload."}, status=400)
        try:
            result = chatbot_gw.chat(
                {
                    "message": payload.get("message", ""),
                    "context": payload.get("context", {}),
                    "history": payload.get("history", []),
                }
            )
        except ApiError as exc:
            return JsonResponse({"message": str(exc)}, status=502)
        return JsonResponse({"data": result}, encoder=DjangoJSONEncoder)


