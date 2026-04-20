You are a senior solution architect, senior backend engineer, and AI/ML engineer.

I am building a microservice-based e-commerce system using Django REST Framework and Docker.

This is a student project, but I want a complete, well-structured, production-inspired design that is still simple enough to implement.

---

# 1. SYSTEM CONTEXT (EXISTING PROJECT)

The system includes the following microservices:

- cloth-service (manage clothing products)
- laptop-service (manage laptop products)
- mobile-service (manage mobile products)
- customer-service (customer auth, cart, checkout, orders)
- staff-service (staff auth, product management)

Tech stack:
- Backend: Django + DRF
- Database: one database per service
- Communication: REST APIs
- Auth: JWT
- Deployment: Docker + Docker Compose

Main features already defined:
- Staff can CRUD products
- Customers can browse, add to cart, checkout
- Payment is mocked (always success)
- Cart supports products from multiple services
- Checkout validates stock and updates stock

---

# 2. PROJECT GOAL (AI EXTENSION)

Now I want to extend this system with AI:

"Analyze customer behavior to provide intelligent product recommendations and build a chatbot for consultation"

The system must include:
- behavior tracking
- recommendation system (model_behavior using ML/DL)
- knowledge base (KB)
- RAG-based chatbot

---

# 3. YOUR TASK

You must guide and design the ENTIRE SYSTEM step-by-step from:

👉 NO AI → FULL AI SYSTEM → RAG CHATBOT

Do NOT jump randomly.
Follow the phases strictly.

---

# PHASE 1: DEFINE AI PROBLEM

1. Clearly define:
   - What is "customer behavior analysis" in this system?
   - What business value does it provide?
   - What are inputs and outputs?

2. Map this problem to my microservices.

---

# PHASE 2: DATA & BEHAVIOR DESIGN

1. Identify all data sources:
   - customer-service (cart, orders)
   - product services
   - user actions

2. Define:
   - what events to track:
     - view product
     - add to cart
     - purchase
   - structure of behavior logs

3. Propose:
   - behavior-service (if needed)
   - database schema for behavior tracking

---

# PHASE 3: AI USE CASES

List and explain:

- product recommendation
- personalized homepage
- related products
- next purchase prediction
- customer segmentation (optional)

For each:
- input
- output
- logic

---

# PHASE 4: AI ARCHITECTURE

Design how AI fits into microservices:

- Do we need:
  - behavior-service
  - recommendation-service

- How services communicate

Provide:
- clear explanation
- Mermaid diagram

---

# PHASE 5: MODEL_BEHAVIOR (ML/DL)

Design a simple but correct AI model:

1. Input format:
   - user_id
   - product_id
   - behavior sequence

2. Output:
   - recommended products

3. Suggest:
   - simple model (rule-based / collaborative filtering)
   - optional deep learning (embedding + dense / LSTM)

4. Explain training flow:
   - offline training
   - saving model
   - inference API

Keep it SIMPLE (student-friendly).

---

# PHASE 6: KNOWLEDGE BASE (KB)

Design KB for chatbot:

- product info
- policies
- FAQ

Define:
- data format (JSON / DB / vector DB)
- examples

---

# PHASE 7: RAG CHATBOT DESIGN

Design chatbot system using RAG:

1. Flow:
   - user question
   - retrieve relevant data
   - generate answer

2. Components:
   - retriever
   - generator (LLM)

3. Where it lives:
   - chatbot-service (new microservice)

---

# PHASE 8: SYSTEM FLOW WITH AI

Describe detailed flows:

### 1. User browsing → tracking behavior
### 2. User homepage → recommendations
### 3. User adds to cart → update model input
### 4. User checkout → update behavior data
### 5. User asks chatbot → RAG flow

---

# PHASE 9: API DESIGN FOR AI SERVICES

Define APIs for:

## behavior-service
- POST /track-event

## recommendation-service
- GET /recommendations/{user_id}

## chatbot-service
- POST /chat

Include:
- request/response
- example JSON

---

# PHASE 10: INTEGRATION WITH EXISTING SYSTEM

Explain:

- how customer-service calls recommendation-service
- how frontend gets recommendations
- how chatbot is integrated

---

# PHASE 11: DEPLOYMENT (DOCKER)

Update system:

- add new services:
  - behavior-service
  - recommendation-service
  - chatbot-service

- update docker-compose

---

# PHASE 12: FINAL ARCHITECTURE

Provide:

- full system architecture
- all services
- data flow
- AI flow

---

# PHASE 13: REPORT-READY EXPLANATION

Write explanation suitable for PDF:

- clear
- structured
- easy to copy into report

---

# CONSTRAINTS

- Keep it understandable for students
- Avoid overengineering
- Use Django-based services
- Keep REST APIs
- AI can be simple but must be correct in concept
- Chatbot must use RAG (not just hardcoded answers)

---

# OUTPUT FORMAT

You must output in order:

1. AI Problem Definition
2. Data Design
3. AI Use Cases
4. Architecture (with diagram)
5. Model Design
6. Knowledge Base
7. RAG Chatbot
8. System Flows
9. APIs
10. Integration
11. Deployment
12. Final Summary

Do NOT generate full code yet.
Focus on system design + explanation.