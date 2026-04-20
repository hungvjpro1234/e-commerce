import uuid

from django.db import models
from django.utils import timezone

from shared.common.product_domains import PRODUCT_SERVICE_CHOICES


class BehaviorEvent(models.Model):
    class EventType(models.TextChoices):
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"
        SEARCH = "search", "Search"
        VIEW_PRODUCT = "view_product", "View Product"
        ADD_TO_CART = "add_to_cart", "Add To Cart"
        UPDATE_CART_QUANTITY = "update_cart_quantity", "Update Cart Quantity"
        REMOVE_FROM_CART = "remove_from_cart", "Remove From Cart"
        PURCHASE = "purchase", "Purchase"

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
    user_id = models.UUIDField()
    session_id = models.CharField(max_length=100, blank=True)
    source_service = models.CharField(max_length=100)
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    product_service = models.CharField(
        max_length=20,
        choices=ProductService.choices,
        blank=True,
    )
    product_id = models.UUIDField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    search_keyword = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-occurred_at", "-created_at"]
        indexes = [
            models.Index(fields=["user_id", "occurred_at"]),
            models.Index(fields=["event_type", "occurred_at"]),
            models.Index(fields=["source_service", "occurred_at"]),
        ]
