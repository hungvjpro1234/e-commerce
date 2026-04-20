from apps.products.models import HomeApplianceProduct


class ProductDomainService:
    @staticmethod
    def get_active_product(product_id):
        return HomeApplianceProduct.objects.filter(id=product_id, is_active=True).first()

    @staticmethod
    def validate_stock(product, quantity):
        return product is not None and product.stock >= quantity

    @staticmethod
    def decrement_stock(product, quantity):
        if product.stock < quantity:
            raise ValueError("Not enough stock.")
        product.stock -= quantity
        product.save(update_fields=["stock", "updated_at"])
        return product
