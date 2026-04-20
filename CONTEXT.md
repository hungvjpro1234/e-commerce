You are a senior solution architect and senior backend engineer. Help me design and implement a complete e-commerce microservice system using Django as backend and Docker for deployment/development.

## 1. Project goal

Build a microservice-based e-commerce system with separate services for different product domains and users.

The system must include these services:

- cloth-service
- laptop-service
- mobile-service
- customer-service
- staff-service

The project uses:
- Backend: Django + Django REST Framework
- Database: each service has its own database
- Containerization: Docker + Docker Compose
- API communication: HTTP REST APIs (keep it simple first)
- Authentication: JWT-based authentication
- Architecture style: microservices
- Language: Python
- Main focus: backend, API design, service boundaries, data flow, dockerized setup, and clean project structure

## 2. Business context

This is an e-commerce system with 2 main actors:

### Staff
Staff has a separate authentication flow and separate interfaces/APIs.
Staff can:
- register
- login
- view own profile
- manage products
- perform CRUD operations on products:
  - create product
  - update product
  - delete product
  - view product list
  - view product detail

### Customer
Customer also has a separate authentication flow and separate interfaces/APIs.
Customer can:
- register
- login
- view own profile
- browse products
- add products to cart
- update cart item quantity
- remove items from cart
- clear cart
- checkout / buy products

### Checkout behavior
Payment logic can be mocked/simulated:
- when customer clicks checkout / pay
- system returns payment success immediately
- cart is cleared after successful payment
- order is created
- product stock is updated accordingly

## 3. Important domain rules

### Product domains
Products are separated into 3 independent domain services:
- cloth-service
- laptop-service
- mobile-service

Each service manages only its own products.

Example:
- cloth-service manages clothing items
- laptop-service manages laptop items
- mobile-service manages mobile phone items

Each product service should support:
- create product
- update product
- delete product
- list products
- get product detail
- manage stock
- manage price
- manage category / brand / description / image URL if needed

### Cart behavior
Customer cart can contain products from multiple product services:
- cloth
- laptop
- mobile

So the cart design must support cross-service product references.

Cart features:
- add item to cart
- update quantity
- delete item
- clear cart
- view cart summary
- validate product existence before adding
- validate stock when checkout happens

### Order / purchase behavior
When checkout happens:
- validate cart is not empty
- validate every product still exists
- validate enough stock
- simulate payment success
- create order record
- reduce stock from the correct product service
- clear cart

For now, payment can be fake/mock:
- no external payment gateway required
- just return success response
- but design the code so that a real payment service can be added later

## 4. Authentication and authorization

There are 2 user domains:
- customer
- staff

I want clear separation between them.

### customer-service
Responsible for:
- customer registration
- customer login
- customer profile
- customer cart
- customer order history if suitable

### staff-service
Responsible for:
- staff registration
- staff login
- staff profile
- authorization for product management actions

Use JWT authentication.

Requirements:
- staff token and customer token should be distinguishable by role or claims
- only staff can create/update/delete products
- customers cannot access staff-only APIs
- staff should not use customer APIs unless explicitly allowed
- enforce role-based access control clearly

## 5. Microservice boundary expectations

Design proper service boundaries.

### cloth-service
Owns:
- cloth product data
- cloth stock
- cloth categories if needed

### laptop-service
Owns:
- laptop product data
- laptop stock
- laptop specifications

### mobile-service
Owns:
- mobile product data
- mobile stock
- mobile specifications

### customer-service
Owns:
- customer accounts
- customer authentication
- cart
- checkout orchestration (or propose better approach if needed)
- customer orders or order references

### staff-service
Owns:
- staff accounts
- staff authentication
- staff permissions / role

If needed, you may propose:
- API Gateway service
- common shared library for JWT validation
- order-service
- payment-service

But only add them if truly necessary and explain why.
If you propose extra services, keep the architecture understandable for a student project.

## 6. Technical expectations

I want the AI to help me generate:

### A. High-level architecture
- explain service responsibilities
- explain communication between services
- explain request flow for:
  - staff managing products
  - customer adding to cart
  - customer checkout
- explain database-per-service principle

### B. Project structure
Generate a practical folder structure for the whole microservice project, for example:
- root folder
- each Django service
- docker-compose.yml
- env files
- requirements files
- shared utilities if needed

### C. Database design
For each service, propose models.

#### Possible models

cloth-service:
- ClothProduct
- ClothCategory

laptop-service:
- LaptopProduct
- LaptopCategory / Brand

mobile-service:
- MobileProduct
- MobileCategory / Brand

customer-service:
- Customer
- Cart
- CartItem
- Order
- OrderItem

staff-service:
- Staff

You may rename models if needed, but keep them clean and practical.

For product models, include common fields such as:
- id
- name
- description
- price
- stock
- image_url
- created_at
- updated_at
- is_active

And product-specific fields where needed.

### D. API design
Define REST APIs for each service.

Examples:

#### customer-service
- POST /api/customers/register
- POST /api/customers/login
- GET /api/customers/profile
- GET /api/cart
- POST /api/cart/items
- PUT /api/cart/items/{id}
- DELETE /api/cart/items/{id}
- DELETE /api/cart/clear
- POST /api/checkout
- GET /api/orders
- GET /api/orders/{id}

#### staff-service
- POST /api/staff/register
- POST /api/staff/login
- GET /api/staff/profile

#### cloth-service
- GET /api/cloth-products
- GET /api/cloth-products/{id}
- POST /api/cloth-products
- PUT /api/cloth-products/{id}
- DELETE /api/cloth-products/{id}

Do the same for laptop-service and mobile-service.

For each endpoint, specify:
- purpose
- request body
- response body
- auth requirement
- role restriction

### E. Inter-service communication
Describe how services communicate.

Examples:
- customer-service checks product detail from cloth/laptop/mobile service before adding to cart
- checkout calls product services to verify stock
- checkout updates stock in corresponding product services
- JWT validation between services

Keep it simple with REST first.
If asynchronous messaging would help, mention it only as an optional future improvement.

### F. Dockerization
Provide Docker setup for all services.

Need:
- Dockerfile for each Django service
- docker-compose.yml for the whole system
- one database per service
- environment variables
- ports for each service

Use a practical local development setup.

### G. Development standards
Use:
- Django REST Framework
- serializers
- views / viewsets
- URL routing
- service layer if helpful
- permissions classes
- clean settings organization
- .env configuration
- requirements.txt

Code should be:
- modular
- readable
- beginner-friendly but still correct
- production-inspired, but not unnecessarily overengineered

## 7. Functional scenarios to support

The design and generated code/documents must support these scenarios:

### Scenario 1: Staff creates product
1. staff registers or logs in
2. staff sends authenticated request
3. staff creates a new cloth/laptop/mobile product
4. product is stored in the correct product service database

### Scenario 2: Staff updates product
1. staff logs in
2. staff edits price, stock, description, etc.
3. product service updates the record

### Scenario 3: Staff deletes product
1. staff logs in
2. staff deletes a product
3. deleted/inactive product should no longer be purchasable

### Scenario 4: Customer adds product to cart
1. customer logs in
2. customer chooses a product from one of the 3 product services
3. customer-service validates product
4. item is added to cart

### Scenario 5: Customer edits cart
1. customer increases/decreases quantity
2. customer removes an item
3. customer clears cart

### Scenario 6: Customer checkout
1. customer clicks pay / checkout
2. system validates cart
3. payment is simulated as successful
4. order is created
5. stock is reduced in the corresponding product services
6. cart is cleared
7. success response is returned

## 8. Non-functional expectations

- Keep the system understandable for a student project
- Do not overcomplicate with Kubernetes or advanced DevOps
- Use clear separation of concerns
- Use database per service
- Avoid tight coupling
- Make it extensible later
- Prefer pragmatic design over unnecessary complexity

## 9. Deliverables I want from you

I want you to help me step by step and generate the following:

1. System architecture explanation
2. Microservice responsibility breakdown
3. Database design / models for each service
4. API contracts for each service
5. Request flow diagrams or textual sequence flows
6. Project folder structure
7. Docker Compose setup
8. Django starter code structure for each service
9. Authentication and permission design
10. Cart and checkout logic design
11. Sample code for critical parts
12. Suggestions for future improvements

## 10. Constraints and preferences

- Keep backend in Django
- Use Docker
- Prefer REST APIs
- Payment is mocked for now
- Separate login/register for staff and customer
- Separate product services by domain: cloth, laptop, mobile
- CRUD operations by staff must directly affect product services
- Customer cart actions and checkout must also reflect actual product data and stock
- Explain tradeoffs clearly if you change or improve the architecture
- When generating code, do it in a way that is consistent across services
- Prioritize correctness, simplicity, and clean boundaries

## 11. Output format I expect from you

Please answer in this order:

1. Proposed final architecture
2. Why this architecture fits the requirements
3. Service-by-service responsibilities
4. Data model design
5. API design
6. Authentication / authorization design
7. Cart and checkout flow
8. Inter-service communication flow
9. Docker/project structure
10. Implementation roadmap
11. Optional improvements

When useful, include:
- Mermaid diagrams
- directory trees
- tables for endpoints
- sample request/response JSON
- starter Django code skeletons

Important:
Do not jump straight into coding everything at once.
First give me the architecture and design.
Then help me generate the project structure and code service by service.