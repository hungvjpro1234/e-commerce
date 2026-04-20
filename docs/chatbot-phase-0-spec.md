# Chatbot AI Phase 0 Spec

This document freezes the implementation conventions for the AI/chatbot work
described in `CHATBOT-IMPLEMENT-PLAN.md`. It is the source of truth for Phase 1
and Phase 2 implementation.

## 1. Locked Decisions

### 1.1 Behavior enum

The only valid behavior values are:

1. `register`
2. `login`
3. `search`
4. `view_product`
5. `add_to_cart`
6. `update_cart_quantity`
7. `remove_from_cart`
8. `purchase`

No alternate names are allowed in stored data or service-to-service payloads.
Existing names such as `cart_add` must be migrated to the canonical enum.

### 1.2 ML task

- Primary task: `next_behavior`
- Input: recent ordered behavior sequence for one user/session
- Output: one of the 8 behavior classes above

### 1.3 Service responsibilities

- `behavior-service`
  - Accept internal event ingest requests
  - Validate and store canonical behavior events
  - Expose list/export APIs for dataset generation
- `recommendation-service`
  - Own preprocessing, model training artifacts, and inference
  - Predict next behavior using `model_best`
  - Convert predicted intent into product recommendations
- `chatbot-service`
  - Retrieve grounded context from KB graph and product data
  - Return chat answers with evidence
- `web-service`
  - Trigger search and product-detail tracking
  - Render recommendation blocks and custom chat UI
- `customer-service`
  - Trigger auth/cart/checkout behavior events

## 2. Canonical Event Contract

### 2.1 Internal ingest endpoint

- Method: `POST /api/internal/events`
- Auth headers:
  - `X-Internal-Service-Token`: must match shared internal token
  - `X-Service-Name`: caller service name, stored as `source_service`

### 2.2 Request payload

```json
{
  "user_id": "uuid-string",
  "session_id": "optional-session-id",
  "event_type": "search",
  "product_service": "cloth",
  "product_id": "optional-product-uuid",
  "category": "optional-category-or-domain",
  "search_keyword": "optional-search-text",
  "quantity": 1,
  "occurred_at": "2026-04-20T14:23:11Z",
  "metadata": {
    "source": "web-service",
    "domain_filter": "cloth"
  }
}
```

### 2.3 Field rules

- `user_id`: required for all events
- `session_id`: optional in Phase 1, but the field must exist in schema for
  future dataset generation and chat analytics
- `event_type`: required; must be one of the 8 canonical behavior values
- `product_service`: required for product-specific events, otherwise nullable
- `product_id`: required for product-specific events, otherwise nullable
- `category`: optional normalized category/domain label; for this codebase the
  current top-level product domain is acceptable as the category value
- `search_keyword`: required for `search`, otherwise nullable
- `quantity`: required for cart and purchase events, otherwise nullable
- `occurred_at`: caller may supply an ISO-8601 timestamp; if omitted,
  `behavior-service` sets it server-side
- `metadata`: required as an object, may be empty

### 2.4 Product-specific event rules

The following events must include `product_service` and `product_id`:

- `view_product`
- `add_to_cart`
- `update_cart_quantity`
- `remove_from_cart`
- `purchase`

### 2.5 Search event rules

`search` events must:

- set `event_type` to `search`
- set `search_keyword` to the submitted search term
- set `category` to the selected domain filter when present
- leave `product_id` null

### 2.6 Register and login event rules

`register` and `login` events must:

- come from `customer-service`
- include `user_id`
- leave `product_service`, `product_id`, and `search_keyword` null
- set `metadata.source` to `customer-service`

### 2.7 Response contract

Phase 1 ingest response must return a simple success payload:

```json
{
  "data": {
    "id": "event-uuid",
    "event_type": "search"
  },
  "message": "Behavior event stored."
}
```

Exact wrapper structure may follow the shared `ok(...)` response style already
used in the repo, but the payload must include the stored event ID and canonical
event type.

## 3. Tracking Points To Implement In Phase 2

### 3.1 `customer-service`

- `POST /api/customers/register`
  - emit `register` after customer is created successfully
- `POST /api/customers/login`
  - emit `login` after credentials are validated successfully
- `POST /api/cart/items`
  - emit `add_to_cart`
- `PUT /api/cart/items/{id}`
  - emit `update_cart_quantity`
- `DELETE /api/cart/items/{id}`
  - emit `remove_from_cart`
- `POST /api/checkout`
  - emit `purchase` once per purchased cart item after order creation succeeds

### 3.2 `web-service`

- `GET /products?q=...`
  - emit `search` only when `q` is non-empty and product listing loads
  - include `search_keyword=q`
  - include selected `domain` as `category` when present
- `GET /products/{domain}/{product_id}`
  - emit `view_product` after product detail loads successfully
  - include `product_service=domain`
  - include `product_id`
  - include `category=domain`

## 4. Migration Mapping From Current Code

### 4.1 Existing behavior emission

Current known behavior emission exists in:

- `services/customer-service/apps/cart/services.py`
  - currently emits `cart_add`
  - currently emits `purchase`

### 4.2 Required migration

- Replace `cart_add` with `add_to_cart`
- Add missing emission in cart update flow as `update_cart_quantity`
- Add missing emission in cart remove flow as `remove_from_cart`
- Add missing emission in customer register flow as `register`
- Add missing emission in customer login flow as `login`
- Add missing emission in web product search flow as `search`
- Add missing emission in web product detail flow as `view_product`

### 4.3 Error-handling rule for emitters

Event emission should be fail-soft for user-facing flows:

- caller flow must not fail only because behavior tracking is unavailable
- payload validation mismatches must not be silently ignored inside
  `behavior-service`
- caller-side request failures should be logged with service/context metadata

This means:

- caller services may catch network/request exceptions and continue
- `behavior-service` must still validate strictly and return 4xx for bad shape

## 5. Phase 1 Implementation Guardrails

Phase 1 must implement the service against this schema directly.

- Do not create a temporary event model with non-canonical enum names
- Do not store `cart_add` or other alias values
- Do not omit `session_id` from the DB model, even if callers do not yet supply
  it
- Do not postpone `category` and `search_keyword` fields to later phases
- Prefer one event table/model with nullable contextual fields over multiple
  partial tables

## 6. Phase 0 Acceptance

Phase 0 is complete when:

- the canonical 8-behavior enum is fixed
- the internal ingest contract is fixed
- required tracking points are fixed
- migration mapping from current code is fixed
- Phase 1 can be implemented without making new product/schema decisions
