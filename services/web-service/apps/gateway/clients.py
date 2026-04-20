from collections import defaultdict

import requests
from django.conf import settings

PRODUCT_DOMAIN_ORDER = (
    "cloth",
    "laptop",
    "mobile",
    "accessory",
    "home-appliance",
    "book",
    "beauty",
    "food",
    "sports",
    "gaming",
)

PRODUCT_SERVICES = {
    "cloth": {
        "base_url": settings.CLOTH_SERVICE_URL,
        "resource": "cloth-products",
        "label": "Cloth",
    },
    "laptop": {
        "base_url": settings.LAPTOP_SERVICE_URL,
        "resource": "laptop-products",
        "label": "Laptop",
    },
    "mobile": {
        "base_url": settings.MOBILE_SERVICE_URL,
        "resource": "mobile-products",
        "label": "Mobile",
    },
    "accessory": {
        "base_url": settings.ACCESSORY_SERVICE_URL,
        "resource": "accessory-products",
        "label": "Tech Accessories",
    },
    "home-appliance": {
        "base_url": settings.HOME_APPLIANCE_SERVICE_URL,
        "resource": "home-appliance-products",
        "label": "Home Appliances",
    },
    "book": {
        "base_url": settings.BOOK_SERVICE_URL,
        "resource": "book-products",
        "label": "Books",
    },
    "beauty": {
        "base_url": settings.BEAUTY_SERVICE_URL,
        "resource": "beauty-products",
        "label": "Beauty",
    },
    "food": {
        "base_url": settings.FOOD_SERVICE_URL,
        "resource": "food-products",
        "label": "Food & Drinks",
    },
    "sports": {
        "base_url": settings.SPORTS_SERVICE_URL,
        "resource": "sports-products",
        "label": "Sports",
    },
    "gaming": {
        "base_url": settings.GAMING_SERVICE_URL,
        "resource": "gaming-products",
        "label": "Gaming",
    },
}


class ApiError(Exception):
    pass


class BaseGatewayClient:
    timeout = 10

    def _request(self, method, url, **kwargs):
        response = requests.request(method, url, timeout=self.timeout, **kwargs)
        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get("message") or str(payload)
            except ValueError:
                message = response.text
            raise ApiError(message or "Request failed.")
        if not response.content:
            return None
        return response.json()


class CustomerGateway(BaseGatewayClient):
    base_url = settings.CUSTOMER_SERVICE_URL

    def register(self, payload):
        return self._request("post", f"{self.base_url}/api/customers/register", json=payload)

    def login(self, payload):
        return self._request("post", f"{self.base_url}/api/customers/login", json=payload)

    def profile(self, token):
        return self._request("get", f"{self.base_url}/api/customers/profile", headers={"Authorization": f"Bearer {token}"})

    def cart(self, token):
        return self._request("get", f"{self.base_url}/api/cart", headers={"Authorization": f"Bearer {token}"})

    def add_cart_item(self, token, payload):
        return self._request("post", f"{self.base_url}/api/cart/items", json=payload, headers={"Authorization": f"Bearer {token}"})

    def update_cart_item(self, token, item_id, payload):
        return self._request("put", f"{self.base_url}/api/cart/items/{item_id}", json=payload, headers={"Authorization": f"Bearer {token}"})

    def delete_cart_item(self, token, item_id):
        return self._request("delete", f"{self.base_url}/api/cart/items/{item_id}", headers={"Authorization": f"Bearer {token}"})

    def clear_cart(self, token):
        return self._request("delete", f"{self.base_url}/api/cart/clear", headers={"Authorization": f"Bearer {token}"})

    def checkout(self, token):
        return self._request("post", f"{self.base_url}/api/checkout", json={}, headers={"Authorization": f"Bearer {token}"})

    def orders(self, token):
        return self._request("get", f"{self.base_url}/api/orders", headers={"Authorization": f"Bearer {token}"})

    def order_detail(self, token, order_id):
        return self._request("get", f"{self.base_url}/api/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})


class StaffGateway(BaseGatewayClient):
    base_url = settings.STAFF_SERVICE_URL

    def login(self, payload):
        return self._request("post", f"{self.base_url}/api/staff/login", json=payload)

    def register(self, payload):
        return self._request("post", f"{self.base_url}/api/staff/register", json=payload)

    def profile(self, token):
        return self._request("get", f"{self.base_url}/api/staff/profile", headers={"Authorization": f"Bearer {token}"})


class ProductGateway(BaseGatewayClient):
    def list_all(self):
        products = []
        for domain in PRODUCT_DOMAIN_ORDER:
            config = PRODUCT_SERVICES[domain]
            payload = self._request("get", f"{config['base_url']}/api/{config['resource']}")
            for item in payload:
                item["domain"] = domain
                item["domain_label"] = config["label"]
                products.append(item)
        return sorted(products, key=lambda item: item.get("name", ""))

    def list_by_domain(self, domain):
        config = PRODUCT_SERVICES[domain]
        payload = self._request("get", f"{config['base_url']}/api/{config['resource']}")
        for item in payload:
            item["domain"] = domain
            item["domain_label"] = config["label"]
        return payload

    def detail(self, domain, product_id):
        config = PRODUCT_SERVICES[domain]
        payload = self._request("get", f"{config['base_url']}/api/{config['resource']}/{product_id}")
        payload["domain"] = domain
        payload["domain_label"] = config["label"]
        return payload

    def create(self, domain, token, payload):
        config = PRODUCT_SERVICES[domain]
        return self._request("post", f"{config['base_url']}/api/{config['resource']}", json=payload, headers={"Authorization": f"Bearer {token}"})

    def update(self, domain, token, product_id, payload):
        config = PRODUCT_SERVICES[domain]
        return self._request("put", f"{config['base_url']}/api/{config['resource']}/{product_id}", json=payload, headers={"Authorization": f"Bearer {token}"})

    def delete(self, domain, token, product_id):
        config = PRODUCT_SERVICES[domain]
        return self._request("delete", f"{config['base_url']}/api/{config['resource']}/{product_id}", headers={"Authorization": f"Bearer {token}"})
