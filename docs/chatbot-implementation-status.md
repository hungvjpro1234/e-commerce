# Chatbot Implementation Status

This file is a compact handoff/context document for testing the chatbot,
recommendation, and behavior-tracking implementation without reading the full
chat history.

## Current Progress

- Phase 0: completed
- Phase 1: completed
- Phase 2: completed
- Phase 3: completed
- Phase 4: completed
- Phase 5: completed
- Phase 6: completed
- Phase 7: completed
- Phase 8: completed
- Phase 9: completed
- Phase 10: pending

## Core Goal

The project extends the existing Django/DRF e-commerce microservice system with
an AI layer that satisfies the assignment requirements:

1. track 8 user behaviors
2. generate `data_user500.csv`
3. train and compare `RNN`, `LSTM`, `biLSTM`
4. choose `model_best`
5. build `KB_Graph` in Neo4j
6. build graph-backed chatbot APIs
7. integrate recommendations into search/cart
8. integrate a custom chat UI into the frontend

## Locked Behavior Enum

The canonical behavior list is:

1. `register`
2. `login`
3. `search`
4. `view_product`
5. `add_to_cart`
6. `update_cart_quantity`
7. `remove_from_cart`
8. `purchase`

Detailed Phase 0 schema/spec lives in `docs/chatbot-phase-0-spec.md`.

## What Exists Now

### behavior-service

Implemented in `services/behavior-service`.

Available APIs:

- `POST /api/internal/events`
- `GET /api/events`
- `GET /api/events/export`

Behavior ingest uses:

- `X-Internal-Service-Token`
- `X-Service-Name`

### Behavior Tracking

Canonical events are already emitted from:

- `customer-service`
  - register
  - login
  - add_to_cart
  - update_cart_quantity
  - remove_from_cart
  - purchase
- `web-service`
  - search
  - view_product

### Dataset

Generated files:

- `docs/sample-data/data_user500.csv`
- `docs/sample-data/data_user500_sample20.csv`

Dataset snapshot:

- `500` users
- `6119` rows
- all `8` behaviors present

### Preprocessing

Generated artifacts:

- `services/recommendation-service/artifacts/preprocessed/train.jsonl`
- `services/recommendation-service/artifacts/preprocessed/val.jsonl`
- `services/recommendation-service/artifacts/preprocessed/test.jsonl`
- `services/recommendation-service/artifacts/preprocessed/encoders.json`
- `services/recommendation-service/artifacts/preprocessed/summary.json`

Summary snapshot:

- `total_samples = 4930`
- `sequence_length = 5`
- `num_classes = 8`

### Model Training

Training artifacts:

- `services/recommendation-service/artifacts/trained_models/model_rnn.pt`
- `services/recommendation-service/artifacts/trained_models/model_lstm.pt`
- `services/recommendation-service/artifacts/trained_models/model_bilstm.pt`
- `services/recommendation-service/artifacts/trained_models/model_best.pt`
- `services/recommendation-service/artifacts/trained_models/training_report.json`
- `services/recommendation-service/artifacts/trained_models/model_comparison.json`
- `services/recommendation-service/artifacts/trained_models/model_comparison.png`

Best model:

- `model_best = biLSTM`

Metric snapshot:

- `RNN weighted_f1 = 0.8931`
- `LSTM weighted_f1 = 0.8956`
- `biLSTM weighted_f1 = 0.8982`

### recommendation-service

Implemented in `services/recommendation-service`.

Available APIs:

- `POST /api/recommend/predict-next-behavior`
- `POST /api/recommend/products`

Behavior:

- loads `model_best.pt`
- predicts next behavior
- returns top product recommendations
- includes explainable `reason_codes`

### Neo4j / KB_Graph

Neo4j is already added to `docker-compose.yml`.

Graph import pipeline:

- `services/chatbot-service/scripts/import_kb_graph.py`

Graph verification summary:

- `users = 500`
- `categories = 10`
- `products = 94`
- `behaviors = 6119`

Artifacts:

- `services/chatbot-service/artifacts/kb_graph_import_summary.json`
- `docs/sample-data/kb_graph_queries.cypher`

### chatbot-service

Implemented in `services/chatbot-service`.

Available APIs:

- `POST /api/chat`
- `POST /api/chat/context`

Behavior:

- queries Neo4j-backed graph context
- returns grounded answers
- includes `evidence`
- supports fallback when graph context is unavailable

### web-service integration

Implemented in `services/web-service`.

What is integrated:

- search-page recommendation block
- cart-page recommendation block
- custom chat widget in `templates/base.html`
- chat proxy endpoints:
  - `POST /chat/context`
  - `POST /chat/message`

Important integration detail:

- `web-service` stores a short `recent_behavior_events` list in session so it
  can send context to recommendation/chat flows without reading directly from
  `behavior-service` in the request path

## Main Files To Know During Testing

- `CHATBOT-IMPLEMENT-PLAN.md`
- `docs/chatbot-phase-0-spec.md`
- `docs/chatbot-implementation-status.md`
- `docker-compose.yml`
- `services/behavior-service`
- `services/recommendation-service`
- `services/chatbot-service`
- `services/web-service/apps/customer_portal/views.py`
- `services/web-service/apps/gateway/clients.py`
- `services/web-service/templates/base.html`

## Tests Already Added

### behavior-service

- `services/behavior-service/apps/events/tests/test_events_api.py`

### customer-service

- `services/customer-service/apps/customers/tests/test_auth.py`
- `services/customer-service/apps/cart/tests/test_cart_checkout.py`

### web-service

- `services/web-service/apps/customer_portal/tests/test_behavior_tracking.py`
- `services/web-service/apps/customer_portal/tests/test_ai_integration.py`

### recommendation-service

- `services/recommendation-service/tests/test_generate_data_user500.py`
- `services/recommendation-service/tests/test_preprocess_behavior_sequences.py`
- `services/recommendation-service/tests/test_train_behavior_models.py`
- `services/recommendation-service/apps/recommendations/tests/test_recommendation_api.py`

### chatbot-service

- `services/chatbot-service/tests/test_import_kb_graph.py`
- `services/chatbot-service/apps/chat/tests/test_chat_api.py`

## Recommended Test Focus Now

If you want to test the current implementation quickly, focus on:

1. search a product in `web-service` and verify recommendation block appears
2. open cart and verify recommendation block appears
3. open the custom chat widget and send product/category/cart questions
4. verify chat responses include grounded product evidence
5. verify Neo4j-backed chatbot still falls back gracefully when retrieval fails

## Remaining Work

Only Phase 10 is still pending:

- final end-to-end validation
- screenshots for report
- final testing notes / reproducible run steps
