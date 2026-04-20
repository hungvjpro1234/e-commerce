from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.gateway.clients import ApiError, ProductGateway, StaffGateway

staff_gw = StaffGateway()
product_gw = ProductGateway()

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

DOMAIN_EXTRA_FIELDS = {
    "cloth": [
        {"name": "size", "label": "Size", "type": "text"},
        {"name": "material", "label": "Material", "type": "text"},
        {"name": "color", "label": "Color", "type": "text"},
        {"name": "gender", "label": "Gender", "type": "text"},
    ],
    "laptop": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "cpu", "label": "CPU", "type": "text"},
        {"name": "ram_gb", "label": "RAM (GB)", "type": "number"},
        {"name": "storage_gb", "label": "Storage (GB)", "type": "number"},
        {"name": "display_size", "label": "Display Size (inches)", "type": "number"},
    ],
    "mobile": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "operating_system", "label": "OS", "type": "text"},
        {"name": "screen_size", "label": "Screen Size (inches)", "type": "number"},
        {"name": "battery_mah", "label": "Battery (mAh)", "type": "number"},
        {"name": "camera_mp", "label": "Camera (MP)", "type": "number"},
    ],
    "accessory": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "accessory_type", "label": "Accessory Type", "type": "text"},
        {"name": "compatibility", "label": "Compatibility", "type": "text"},
        {"name": "wireless", "label": "Wireless", "type": "text"},
        {"name": "warranty_months", "label": "Warranty (months)", "type": "number"},
    ],
    "home-appliance": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "power_watt", "label": "Power (W)", "type": "number"},
        {"name": "capacity", "label": "Capacity", "type": "text"},
        {"name": "energy_rating", "label": "Energy Rating", "type": "text"},
        {"name": "appliance_type", "label": "Appliance Type", "type": "text"},
    ],
    "book": [
        {"name": "author", "label": "Author", "type": "text"},
        {"name": "publisher", "label": "Publisher", "type": "text"},
        {"name": "language", "label": "Language", "type": "text"},
        {"name": "page_count", "label": "Page Count", "type": "number"},
        {"name": "genre", "label": "Genre", "type": "text"},
    ],
    "beauty": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "skin_type", "label": "Skin Type", "type": "text"},
        {"name": "volume_ml", "label": "Volume (ml)", "type": "number"},
        {"name": "expiry_months", "label": "Shelf Life (months)", "type": "number"},
        {"name": "origin_country", "label": "Origin Country", "type": "text"},
    ],
    "food": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "weight_g", "label": "Weight (g)", "type": "number"},
        {"name": "flavor", "label": "Flavor", "type": "text"},
        {"name": "expiry_date", "label": "Expiry Date", "type": "date"},
        {"name": "is_organic", "label": "Organic", "type": "text"},
    ],
    "sports": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "sport_type", "label": "Sport Type", "type": "text"},
        {"name": "material", "label": "Material", "type": "text"},
        {"name": "size", "label": "Size", "type": "text"},
        {"name": "target_gender", "label": "Target Gender", "type": "text"},
    ],
    "gaming": [
        {"name": "brand", "label": "Brand", "type": "text"},
        {"name": "platform", "label": "Platform", "type": "text"},
        {"name": "connectivity", "label": "Connectivity", "type": "text"},
        {"name": "rgb_support", "label": "RGB Support", "type": "text"},
        {"name": "warranty_months", "label": "Warranty (months)", "type": "number"},
    ],
}


def require_staff(view_method):
    def wrapper(self, request, *args, **kwargs):
        if not request.session.get("staff_access_token"):
            return redirect("/staff/login")
        return view_method(self, request, *args, **kwargs)
    wrapper.__name__ = view_method.__name__
    return wrapper


def _collect_product_form(request, domain):
    data = {
        "name": request.POST.get("name"),
        "description": request.POST.get("description", ""),
        "price": request.POST.get("price"),
        "stock": int(request.POST.get("stock", 0)),
        "image_url": request.POST.get("image_url", ""),
        "is_active": request.POST.get("is_active") == "on",
    }
    for field in DOMAIN_EXTRA_FIELDS.get(domain, []):
        val = request.POST.get(field["name"])
        if val is not None:
            if field["type"] == "number":
                try:
                    data[field["name"]] = float(val) if "." in (val or "") else int(val)
                except (ValueError, TypeError):
                    data[field["name"]] = val
            else:
                data[field["name"]] = val
    return data


class StaffLoginView(View):
    def get(self, request):
        if request.session.get("staff_access_token"):
            return redirect("/staff/dashboard")
        return render(request, "staff_portal/login.html")

    def post(self, request):
        try:
            resp = staff_gw.login({
                "email": request.POST.get("email"),
                "password": request.POST.get("password"),
            })
            data = resp.get("data", {})
            request.session["staff_access_token"] = data["access_token"]
            request.session["staff_profile"] = data["user"]
            messages.success(request, f"Welcome, {data['user']['full_name']}!")
            return redirect("/staff/dashboard")
        except ApiError as exc:
            messages.error(request, str(exc))
            return render(request, "staff_portal/login.html")


class StaffLogoutView(View):
    def get(self, request):
        request.session.pop("staff_access_token", None)
        request.session.pop("staff_profile", None)
        return redirect("/")


class DashboardView(View):
    @require_staff
    def get(self, request):
        counts = {}
        for domain in DOMAIN_ORDER:
            try:
                counts[domain] = len(product_gw.list_by_domain(domain))
            except ApiError:
                counts[domain] = "?"
        return render(request, "staff_portal/dashboard.html", {
            "counts": counts,
            "staff": request.session.get("staff_profile"),
            "domain_labels": DOMAIN_LABELS,
            "domain_order": DOMAIN_ORDER,
        })


class ProductListView(View):
    @require_staff
    def get(self, request, domain):
        if domain not in DOMAIN_LABELS:
            return redirect("/staff/dashboard")
        try:
            products = product_gw.list_by_domain(domain)
        except ApiError as exc:
            messages.error(request, str(exc))
            products = []
        return render(request, "staff_portal/product_list.html", {
            "products": products,
            "domain": domain,
            "domain_label": DOMAIN_LABELS[domain],
            "domain_labels": DOMAIN_LABELS,
            "domain_order": DOMAIN_ORDER,
        })


class ProductCreateView(View):
    @require_staff
    def get(self, request, domain):
        if domain not in DOMAIN_LABELS:
            return redirect("/staff/dashboard")
        return render(request, "staff_portal/product_form.html", {
            "domain": domain,
            "domain_label": DOMAIN_LABELS[domain],
            "extra_fields": DOMAIN_EXTRA_FIELDS.get(domain, []),
            "action": "Create",
            "product": {},
        })

    @require_staff
    def post(self, request, domain):
        token = request.session["staff_access_token"]
        data = _collect_product_form(request, domain)
        try:
            product_gw.create(domain, token, data)
            messages.success(request, "Product created.")
            return redirect(f"/staff/products/{domain}")
        except ApiError as exc:
            messages.error(request, str(exc))
            return render(request, "staff_portal/product_form.html", {
                "domain": domain,
                "domain_label": DOMAIN_LABELS[domain],
                "extra_fields": DOMAIN_EXTRA_FIELDS.get(domain, []),
                "action": "Create",
                "product": data,
            })


class ProductEditView(View):
    @require_staff
    def get(self, request, domain, product_id):
        if domain not in DOMAIN_LABELS:
            return redirect("/staff/dashboard")
        try:
            product = product_gw.detail(domain, product_id)
        except ApiError as exc:
            messages.error(request, str(exc))
            return redirect(f"/staff/products/{domain}")
        return render(request, "staff_portal/product_form.html", {
            "domain": domain,
            "domain_label": DOMAIN_LABELS[domain],
            "extra_fields": DOMAIN_EXTRA_FIELDS.get(domain, []),
            "action": "Edit",
            "product": product,
        })

    @require_staff
    def post(self, request, domain, product_id):
        if domain not in DOMAIN_LABELS:
            return redirect("/staff/dashboard")
        token = request.session["staff_access_token"]
        data = _collect_product_form(request, domain)
        try:
            product_gw.update(domain, token, product_id, data)
            messages.success(request, "Product updated.")
            return redirect(f"/staff/products/{domain}")
        except ApiError as exc:
            messages.error(request, str(exc))
            return render(request, "staff_portal/product_form.html", {
                "domain": domain,
                "domain_label": DOMAIN_LABELS[domain],
                "extra_fields": DOMAIN_EXTRA_FIELDS.get(domain, []),
                "action": "Edit",
                "product": data,
            })


class ProductDeleteView(View):
    @require_staff
    def post(self, request, domain, product_id):
        if domain not in DOMAIN_LABELS:
            return redirect("/staff/dashboard")
        token = request.session["staff_access_token"]
        try:
            product_gw.delete(domain, token, product_id)
            messages.success(request, "Product deactivated.")
        except ApiError as exc:
            messages.error(request, str(exc))
        return redirect(f"/staff/products/{domain}")
