from django.db import transaction
from django.utils import timezone

from apps.behavior.models import BehaviorEvent, UserItemAggregate


class BehaviorTracker:
    def track_event(self, *, user_id, product_id, product_service, event_type, quantity=1, metadata=None):
        metadata = dict(metadata or {})
        with transaction.atomic():
            event = BehaviorEvent.objects.create(
                user_id=user_id,
                product_id=product_id,
                product_service=product_service,
                event_type=event_type,
                quantity=quantity,
                metadata=metadata,
            )
            aggregate, _ = UserItemAggregate.objects.get_or_create(
                user_id=user_id,
                product_id=product_id,
                product_service=product_service,
            )
            aggregate.last_event_type = event_type
            aggregate.last_event_at = timezone.now()
            aggregate.total_quantity += quantity
            if event_type == "product_view":
                aggregate.view_count += 1
            elif event_type == "cart_add":
                aggregate.cart_add_count += 1
            elif event_type == "purchase":
                aggregate.purchase_count += 1
            aggregate.save()
        return event
