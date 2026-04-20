# E-Commerce Microservice System

This repository contains a Django + Django REST Framework microservice-based
e-commerce backend for a student-friendly but production-inspired architecture.

## Services

- `staff-service`: staff registration, login, profile, and product-management authority
- `customer-service`: customer registration, login, profile, cart, checkout, orders
- `cloth-service`: clothing catalog and stock
- `laptop-service`: laptop catalog and stock
- `mobile-service`: mobile catalog and stock
- `accessory-service`: tech accessories catalog and stock
- `home-appliance-service`: home appliances catalog and stock
- `book-service`: books catalog and stock
- `beauty-service`: beauty catalog and stock
- `food-service`: food and drinks catalog and stock
- `sports-service`: sports catalog and stock
- `gaming-service`: gaming catalog and stock

## Architecture Summary

- Microservices with database-per-service
- Docker Compose for local development
- JWT-based authentication with explicit `user_type` claims
- REST calls between services for cart validation and checkout orchestration
- Shared Python package for common settings, auth helpers, and service contracts

See `docs/architecture.md` for the full architecture and `docs/api-contracts.md`
for the API contracts.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Review ports and database credentials.
3. Build and start the stack with Docker Compose.
4. Run migrations inside each service container.

```bash
docker compose up --build
```



## Repository Layout

```text
.
|-- docker-compose.yml
|-- docs/
|   |-- architecture.md
|   `-- api-contracts.md
|-- shared/
|-- services/
|   |-- staff-service/
|   |-- customer-service/
|   |-- cloth-service/
|   |-- laptop-service/
|   |-- mobile-service/
|   |-- accessory-service/
|   |-- home-appliance-service/
|   |-- book-service/
|   |-- beauty-service/
|   |-- food-service/
|   |-- sports-service/
|   `-- gaming-service/
`-- tests/
```
