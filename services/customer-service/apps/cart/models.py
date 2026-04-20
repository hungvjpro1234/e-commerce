import uuid

from django.db import models
from shared.common.product_domains import PRODUCT_SERVICE_CHOICES


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CHECKED_OUT = "checked_out", "Checked Out"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="carts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class CartItem(models.Model):
    class ProductService(models.TextChoices):
        CLOTH = PRODUCT_SERVICE_CHOICES[0]
        LAPTOP = PRODUCT_SERVICE_CHOICES[1]
        MOBILE = PRODUCT_SERVICE_CHOICES[2]
        ACCESSORY = PRODUCT_SERVICE_CHOICES[3]
        HOME_APPLIANCE = PRODUCT_SERVICE_CHOICES[4]
        BOOK = PRODUCT_SERVICE_CHOICES[5]
        BEAUTY = PRODUCT_SERVICE_CHOICES[6]
        FOOD = PRODUCT_SERVICE_CHOICES[7]
        SPORTS = PRODUCT_SERVICE_CHOICES[8]
        GAMING = PRODUCT_SERVICE_CHOICES[9]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_service = models.CharField(max_length=20, choices=ProductService.choices)
    product_id = models.UUIDField()
    product_name_snapshot = models.CharField(max_length=255)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url_snapshot = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ("cart", "product_service", "product_id")


class Order(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_service = models.CharField(max_length=20)
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
