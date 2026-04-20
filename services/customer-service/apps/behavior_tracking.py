import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def emit_behavior_event(
    *,
    user_id,
    event_type,
    product_service="",
    product_id=None,
    category="",
    search_keyword="",
    quantity=None,
    session_id="",
    metadata=None,
):
    payload = {
        "user_id": str(user_id),
        "session_id": session_id or "",
        "event_type": event_type,
        "product_service": product_service or "",
        "product_id": str(product_id) if product_id else None,
        "category": category or "",
        "search_keyword": search_keyword or "",
        "quantity": quantity,
        "metadata": metadata or {},
    }

    try:
        response = requests.post(
            f"{settings.BEHAVIOR_SERVICE_URL}/api/internal/events",
            json=payload,
            headers={
                "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
                "X-Service-Name": settings.SERVICE_NAME,
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.warning(
            "Behavior event emit failed",
            extra={
                "service": settings.SERVICE_NAME,
                "event_type": event_type,
                "user_id": str(user_id),
            },
            exc_info=True,
        )
