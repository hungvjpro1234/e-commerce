# CHATBOT-IMPLEMENT-PLAN

## 1. Project Goal

Implement the missing AI layer for the existing Django/DRF microservice e-commerce system so it satisfies the assignment requirements:

1. Generate `data_user500.csv` with **500 users + 8 behaviors**
2. Train and compare **RNN, LSTM, biLSTM**
3. Choose **model_best**
4. Build **KB_Graph** with **Neo4j**
5. Build **RAG + chat** based on KB_Graph
6. Integrate into the e-commerce system:
   - product recommendation when user **searches**
   - product recommendation when user **adds to cart**
   - a **custom chat UI** for users

This plan is based on the current repository state:
- Core e-commerce microservices already exist and run
- AI services are still missing or placeholder-level
- Neo4j is not yet integrated
- No completed behavior-event pipeline or model-training pipeline yet.

---

## 2. Current System State

### Existing foundation
The repository already has a real e-commerce backend with Django + DRF microservices and Docker Compose, including:
- `web-service`
- `customer-service`
- multiple product services
- shared auth/helpers/contracts

The system already supports real e-commerce flows such as product listing/detail, cart, checkout, and orders through the existing services and UI/BFF layer.

### Missing AI pieces
The following parts are not fully implemented yet:
- `behavior-service`
- `recommendation-service`
- `chatbot-service`
- model training pipeline
- Neo4j integration
- recommendation/chat APIs
- custom chat UI end-to-end integration.

---

## 3. Final Functional Scope

### 3.1 Eight behaviors to use
Use the following 8 behaviors because they best fit the current e-commerce flow and are realistic for the assignment:

1. `register`
2. `login`
3. `search`
4. `view_product`
5. `add_to_cart`
6. `update_cart_quantity`
7. `remove_from_cart`
8. `purchase`

This set is aligned with the current repo analysis and is practical for data generation, model training, graph construction, and demo integration.

### 3.2 ML task
Use **next behavior prediction** as the main supervised learning task:

- **Input:** recent user behavior sequence
- **Output:** next behavior among the 8 classes

This is the most practical choice because it fits sequence models naturally and is easier to explain and demo than more complex recommendation objectives.

### 3.3 KB Graph scope
Build the graph around these main entities:

- `User`
- `Behavior`
- `Product`
- `Category`

Main relationships can include:
- `(:User)-[:PERFORMED]->(:Behavior)`
- `(:Behavior)-[:ON_PRODUCT]->(:Product)`
- `(:Product)-[:BELONGS_TO]->(:Category)`
- optional: `(:User)-[:INTERESTED_IN]->(:Category)`

---

## 4. High-Level Architecture Target

### New or completed services
The target implementation should include:

- **behavior-service**
  - receives and stores user events
  - exports event data for dataset generation

- **recommendation-service**
  - owns preprocessing, training artifacts, and inference APIs
  - uses `model_best` for behavior prediction
  - returns recommended products

- **chatbot-service**
  - handles chat requests
  - queries Neo4j / KB_Graph
  - performs RAG-style response generation
  - exposes chat API for the frontend

### Existing services to integrate
- **web-service**
  - acts as UI/BFF
  - calls recommendation/chat APIs
  - renders recommendation blocks and custom chat UI

- **customer-service**
  - emits cart/checkout/auth-related behavior events

- **product services**
  - provide product metadata and category/product details
  - serve as source data for recommendations and KB graph

### Required infrastructure updates
To make this plan executable in the current repository, `docker-compose.yml` must be updated to include:

- `behavior-service` + `behavior-db`
- `recommendation-service` + `recommendation-db`
- `chatbot-service` (and optionally use existing `chatbot-db` if persistent chat data is needed)
- health checks or startup dependency order for AI services and Neo4j

This is mandatory because these three AI services are currently placeholder-level and do not have active runtime definitions in Compose.

---

## 5. Implementation Phases

## Phase 0 — Freeze scope and conventions

### Goal
Lock the design choices before coding.

### Tasks
- Confirm the 8 behaviors
- Confirm the ML task: `next_behavior`
- Confirm graph entities and relationships
- Confirm service responsibilities:
  - behavior-service = event storage
  - recommendation-service = ML + recommendation
  - chatbot-service = RAG + graph chat
  - web-service = UI integration

### Deliverables
- finalized behavior enum
- finalized event schema
- finalized service responsibility note

### Priority
P0

---

## Phase 1 — Implement behavior-service foundation

### Goal
Create a real microservice that can receive and store behavior events from existing services.

### Main files to inspect/update
- `docker-compose.yml`
- `services/behavior-service/*` (new service skeleton, app, routes, models, serializers, settings)
- `.env.example` (ensure behavior-service and behavior-db variables are complete)

### Required ingest contract (must match existing caller)
The behavior ingest API must support:

- `POST /api/internal/events`
- Internal token auth using `X-Internal-Service-Token`
- `X-Service-Name` caller header

Reason: `customer-service` already posts behavior events to `/api/internal/events`.

### Deliverables
- running `behavior-service`
- event model + migrations
- internal ingest endpoint `POST /api/internal/events`
- basic list/export endpoints for dataset generation

### Priority
P0

---

## Phase 2 — Add behavior tracking points

### Goal
Make the current e-commerce system emit all 8 required behavior types.

### Main files to inspect/update
- `services/web-service/apps/customer_portal/views.py`
- `services/web-service/apps/gateway/clients.py`
- `services/customer-service/apps/cart/services.py`
- `services/customer-service/apps/cart/models.py`
- `services/customer-service/apps/customers/views.py`

### Required tracking points
Track these events in the following places:

- `register` (customer registration flow)
- `login` (customer login flow)
- `search` (when user searches products in `web-service`)
- `view_product` (when user opens product detail page in `web-service`)
- `add_to_cart` (already available in `customer-service`)
- `update_cart_quantity` (customer-service cart update flow)
- `remove_from_cart` (customer-service cart remove flow)
- `purchase` (already available after successful checkout)

### Storage
Use PostgreSQL for consistency with the existing microservice architecture.

### Deliverables
- tracking hooks at all required flow points
- event payload contract defined and used consistently
- no silent mismatch between emitted endpoint and ingest endpoint

### Priority
P0

---

## Phase 3 — Generate `data_user500.csv`

### Goal
Satisfy the assignment requirement for the dataset.

### Strategy
Use a hybrid approach:
- reuse real product/category structure from the current e-commerce system
- reuse any real tracked events if available
- generate synthetic users and sessions to reach 500 users
- simulate realistic behavior sequences using simple rules

### Example sequence patterns
- `register -> login -> search -> view_product -> add_to_cart -> purchase`
- `login -> search -> view_product -> view_product -> add_to_cart -> remove_from_cart`
- `login -> search -> add_to_cart -> update_cart_quantity -> purchase`

### Suggested CSV columns
- `user_id`
- `session_id`
- `timestamp`
- `behavior_type`
- `product_id`
- `category`
- `search_keyword`
- `step_in_session`
- `label_next_behavior`

### Notes
The assignment explicitly asks for 500 users and 8 behaviors, so synthetic generation is acceptable as long as it is documented clearly and is consistent with the system’s domain.

### Deliverables
- `data_user500.csv`
- sample 20 rows ready for screenshots in the report

### Priority
P0

---

## Phase 4 — Preprocess sequence data

### Goal
Prepare data for RNN/LSTM/biLSTM training.

### Tasks
- encode behavior labels to integers
- optionally encode category/product features
- group events by `user_id` or `session_id`
- sort by timestamp
- build sequence windows

### Recommended training format
- sequence length: 4 to 6 recent behaviors
- target: next behavior class

### Split
- train / validation / test

### Deliverables
- preprocessing script
- saved encoders/mappings
- train/val/test datasets
- class distribution summary

### Priority
P0

---

## Phase 5 — Train and evaluate RNN / LSTM / biLSTM

### Goal
Complete the model-comparison requirement.

### Location
Put training code and artifacts inside `recommendation-service` or a clear subfolder owned by it, because that service will later host inference.

### Models
- Simple RNN
- LSTM
- biLSTM

### Metrics
At minimum:
- Accuracy
- Precision
- Recall
- F1-score

Optional but recommended:
- confusion matrix
- per-class metrics

### Visualizations
- train loss
- validation loss
- train accuracy
- validation accuracy
- comparison chart across the 3 models

### Best model rule
Choose `model_best` using:
- highest F1-score
- or highest accuracy if the classes are reasonably balanced

Explain the final choice clearly in the report. The assignment explicitly asks for model comparison, best-model selection, and visual plots.

### Deliverables
- `model_rnn`
- `model_lstm`
- `model_bilstm`
- `model_best`
- evaluation report + plots

### Priority
P0

---

## Phase 6 — Build recommendation-service inference API

### Goal
Use the trained model and return product recommendations in the running system.

### Recommended APIs
- `POST /api/recommend/predict-next-behavior`
- `POST /api/recommend/products`

### Recommended logic
Keep the recommendation logic practical and demo-friendly:

- predict next behavior using `model_best`
- derive recommendation strategy from predicted intent
- retrieve candidate products from matching category or related category
- return top-N products

### Example rules
- predicted `view_product` or `add_to_cart`
  - recommend products from same category

- user searched keyword/category
  - recommend products matching search context

- user added a product to cart
  - recommend related products or same-category products

### Why this approach
The assignment requires visible integration in the e-commerce UI, not a research-grade recommender system. A hybrid approach of sequence prediction + rule-based product retrieval is easier to build, explain, and demo.

### Runtime requirement
`recommendation-service` and `recommendation-db` must be added to `docker-compose.yml` before integration testing.

### Deliverables
- working inference API
- top-N recommendation response format
- integration-ready JSON for frontend

### Priority
P1

---

## Phase 7 — Add Neo4j and build KB_Graph

### Goal
Satisfy the graph requirement using real e-commerce entities and behavior data.

### Required infrastructure task
Update `docker-compose.yml` to add:
- `neo4j`
- ports `7474` and `7687`
- persistent volume
- auth environment variables

The current repository does not yet include Neo4j in Docker Compose, so this is a required new addition.

### Data sources for graph
- `data_user500.csv`
- product catalog data from product services
- optional customer/order-derived metadata

### Graph import tasks
- create graph schema
- write import script
- verify graph in Neo4j Browser
- prepare sample Cypher queries for screenshots/report

### Deliverables
- Neo4j service in compose
- import script
- populated KB_Graph
- screenshots of graph + queries

### Priority
P1

---

## Phase 8 — Implement chatbot-service with graph-based RAG

### Goal
Build a chatbot service that answers user questions using KB_Graph and product context.

### Recommended minimal API
- `POST /api/chat`
- `POST /api/chat/context`

### Retrieval strategy
Keep it manageable:
- parse user request
- query Neo4j and/or product data
- assemble factual context
- pass context into the answer generation step
- return structured answer to UI

### Supported question types
- product discovery
- same-category suggestions
- similar-item suggestions
- category explanation
- cart-related suggestions
- shopping assistance

### Important note
A simple graph-retrieval-based context assembly is sufficient for the assignment as long as the chatbot clearly uses KB_Graph-backed information. The assignment specifically asks for “RAG + chat based on KB_Graph.”

### Grounded-answer acceptance criteria
For demo acceptance, each chatbot response should include:
- answer text
- `evidence` list (IDs/titles of products/categories or graph nodes used)
- optional debug field with query trace in development mode

Minimum validation:
- at least 10 test prompts
- at least 8/10 responses include non-empty evidence linked to KB/product data
- fallback response when no relevant graph context is found

### Runtime requirement
`chatbot-service` (and optional `chatbot-db`) must be added to `docker-compose.yml` before web integration.

### Deliverables
- running `chatbot-service`
- retrieval logic
- graph query layer
- chat API returning grounded answers

### Priority
P1

---

## Phase 9 — Integrate recommendation and chat into web-service

### Goal
Expose the AI features in the actual e-commerce frontend.

### Main integration files
- `services/web-service/apps/customer_portal/views.py`
- `services/web-service/apps/gateway/clients.py`
- `services/web-service/templates/base.html`
- `services/web-service/templates/customer_portal/products.html`
- `services/web-service/templates/customer_portal/product_detail.html`
- `services/web-service/templates/customer_portal/cart.html`

### Required UI integrations

#### Search page integration
When user performs search:
- call recommendation API
- render a recommendation block such as:
  - “Recommended for you”
  - “You may also like”

#### Cart integration
When user adds to cart or visits cart:
- call recommendation API
- render related recommendations

#### Chat integration
Add a custom chat interface:
- embedded chat widget or dedicated chat panel/page
- frontend must not resemble the default ChatGPT interface
- use AJAX/fetch to call `chatbot-service`

### Deliverables
- recommendation block on search flow
- recommendation block on cart flow
- custom chat UI connected to chatbot API

### Priority
P0/P1

---

## Phase 10 — Testing, screenshots, and report assets

### Goal
Prepare clean final submission material.

### Required evidence to collect
- screenshot of `data_user500.csv` sample rows
- screenshots/code for model training
- metric comparison table
- plots of 3 models
- proof of `model_best`
- screenshot of Neo4j graph
- screenshot of chat results
- screenshot of recommendation on search page
- screenshot of recommendation on cart page
- screenshot of custom chat UI

These deliverables map directly to the assignment’s PDF submission expectations.

### Deliverables
- final screenshots
- final report notes
- final reproducible run steps

### Priority
P0

---

## 6. Suggested File/Service Execution Order

Use this implementation order to reduce risk:

1. finalize 8 behaviors and schemas
2. update `docker-compose.yml` for AI runtime scaffolding (behavior/recommendation/chatbot + related DBs where needed)
3. implement `behavior-service`
4. add tracking to `web-service` and `customer-service`
5. validate event ingest end-to-end (`customer-service` -> `behavior-service`)
6. generate `data_user500.csv`
7. preprocess data
8. train RNN / LSTM / biLSTM
9. choose `model_best`
10. implement `recommendation-service`
11. add Neo4j to Docker Compose
12. populate KB_Graph
13. implement `chatbot-service`
14. integrate recommendation/chat into `web-service`
15. test, polish UI, collect report screenshots

---

## 7. Priority Summary

### Must finish first
- behavior tracking
- `behavior-service`
- `data_user500.csv`
- RNN / LSTM / biLSTM training
- `model_best`

### Must finish for full assignment compliance
- Neo4j KB_Graph
- chatbot-service with graph-backed chat
- recommendation integration in search/cart
- custom chat UI

### Can be kept simple
- recommendation ranking sophistication
- long conversation memory
- advanced graph schema complexity
- advanced RAG orchestration

---

## 8. Practical Timeline Suggestion

### Day 1
- freeze behavior schema
- implement behavior-service
- add tracking hooks

### Day 2
- generate `data_user500.csv`
- preprocess
- train 3 models
- choose `model_best`

### Day 3
- add Neo4j
- import graph
- verify KB_Graph

### Day 4
- implement recommendation-service
- implement chatbot-service baseline

### Day 5
- integrate into web-service
- test end-to-end flows
- collect screenshots
- write report material

---

## 9. Key Design Principles for the AI Agent

When implementing, the agent should follow these rules:

- Do not redesign the whole system unnecessarily
- Reuse the existing Django/DRF microservice structure
- Keep each new service minimal and demo-ready
- Prefer clear APIs over overly complex internals
- Prefer reproducibility and screenshots over theoretical complexity
- Keep recommendation logic simple and explainable
- Keep chatbot grounded in graph/product facts
- Always optimize for:
  - working demo
  - report screenshots
  - student assignment clarity

---

## 10. Definition of Done

The implementation is considered complete when all of the following are true:

- `behavior-service` stores events successfully
- `data_user500.csv` exists with 500 users and 8 behaviors
- RNN, LSTM, biLSTM are trained and compared
- `model_best` is selected with evidence
- Neo4j runs in Docker Compose
- KB_Graph is populated and queryable
- `chatbot-service` answers using KB_Graph-backed context
- `recommendation-service` returns product suggestions
- `web-service` shows recommendations on search/cart
- `web-service` includes a custom chat UI
- screenshots and outputs are ready for the PDF submission

---

## 11. Next Immediate Step

The next best implementation step is:

**Start with `behavior-service` and event tracking integration.**

Reason:
- it unlocks dataset generation
- it unlocks CSV export
- it creates the base for both ML and graph
- it is the least risky starting point
- it aligns with the current system gaps identified in the repo analysis.
