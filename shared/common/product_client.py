import requests

from shared.common.service_registry import PRODUCT_SERVICE_MAP


class ProductServiceClient:
    def __init__(self, internal_service_token):
        self.internal_service_token = internal_service_token

    def _get_config(self, product_service):
        config = PRODUCT_SERVICE_MAP.get(product_service)
        if not config:
            raise ValueError(f"Unsupported product service: {product_service}")
        return config

    def _headers(self):
        return {
            "X-Internal-Service-Token": self.internal_service_token,
            "X-Service-Name": "customer-service",
        }

    def get_product(self, product_service, product_id):
        config = self._get_config(product_service)
        response = requests.get(
            f"{config['base_url']}/api/{config['resource']}/{product_id}",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def validate_product(self, product_service, product_id, quantity):
        config = self._get_config(product_service)
        response = requests.post(
            f"{config['base_url']}/api/internal/products/validate",
            json={"product_id": product_id, "quantity": quantity},
            headers=self._headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def decrement_stock(self, product_service, product_id, quantity):
        config = self._get_config(product_service)
        response = requests.post(
            f"{config['base_url']}/api/internal/products/decrement-stock",
            json={"product_id": product_id, "quantity": quantity},
            headers=self._headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
