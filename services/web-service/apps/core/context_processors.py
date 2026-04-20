def app_context(request):
    return {
        "is_staff_logged_in": bool(request.session.get("staff_access_token")),
        "is_customer_logged_in": bool(request.session.get("customer_access_token")),
        "staff_profile": request.session.get("staff_profile"),
        "customer_profile": request.session.get("customer_profile"),
        "chat_context": {
            "domain": "",
            "page_context": "global_widget",
            "product_id": "",
        },
        "catalog_domains": (
            ("cloth", "Cloth"),
            ("laptop", "Laptop"),
            ("mobile", "Mobile"),
            ("accessory", "Tech Accessories"),
            ("home-appliance", "Home Appliances"),
            ("book", "Books"),
            ("beauty", "Beauty"),
            ("food", "Food & Drinks"),
            ("sports", "Sports"),
            ("gaming", "Gaming"),
        ),
    }
