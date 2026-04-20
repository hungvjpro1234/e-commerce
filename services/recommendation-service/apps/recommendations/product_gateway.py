import requests

from shared.common.product_domains import PRODUCT_DOMAIN_CONFIG, PRODUCT_DOMAIN_ORDER


class ProductCatalogGateway:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def list_all(self):
        products = []
        for domain in PRODUCT_DOMAIN_ORDER:
            config = PRODUCT_DOMAIN_CONFIG[domain]
            response = requests.get(f"http://{config['service_name']}:8000/api/{config['resource']}", timeout=self.timeout)
            response.raise_for_status()
            for item in response.json():
                if not item.get("is_active", True):
                    continue
                item["domain"] = domain
                item["domain_label"] = config["label"]
                products.append(item)
        return products
