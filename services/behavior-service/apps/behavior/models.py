import uuid

from django.db import models


class BehaviorEvent(models.Model):
    EVENT_CHOICES = [("product_view", "Product View"), ("cart_add", "Cart Add"), ("purchase", "Purchase")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    product_id = models.UUIDField()
    product_service = models.CharField(max_length=32)
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class UserItemAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    product_id = models.UUIDField()
    product_service = models.CharField(max_length=32)
    last_event_type = models.CharField(max_length=32, blank=True, default="")
    view_count = models.PositiveIntegerField(default=0)
    cart_add_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)
    total_quantity = models.PositiveIntegerField(default=0)
    last_event_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [("user_id", "product_service", "product_id")]
