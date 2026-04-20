# API Contracts

This document defines the v1 REST contracts for the e-commerce microservices.

## `staff-service`

### `POST /api/staff/register`

- Purpose: create a new staff account
- Auth: public
- Request:

```json
{
  "email": "admin@example.com",
  "password": "strong-password",
  "full_name": "Store Admin"
}
```

- Response:

```json
{
  "id": "uuid",
  "email": "admin@example.com",
  "full_name": "Store Admin",
  "role": "manager"
}
```

### `POST /api/staff/login`

- Purpose: authenticate staff and return JWT tokens
- Auth: public

### `GET /api/staff/profile`

- Purpose: return current staff profile
- Auth: `staff` token

## `customer-service`

### `POST /api/customers/register`

- Purpose: create a customer account
- Auth: public

### `POST /api/customers/login`

- Purpose: authenticate customer and return JWT tokens
- Auth: public

### `GET /api/customers/profile`

- Purpose: return current customer profile
- Auth: `customer` token

### `GET /api/cart`

- Purpose: return active cart with totals
- Auth: `customer` token

### `POST /api/cart/items`

- Purpose: add an item from a product service to the cart
- Auth: `customer` token
- Request:

```json
{
  "product_service": "cloth",
  "product_id": "uuid",
  "quantity": 2
}
```

### `PUT /api/cart/items/{id}`

- Purpose: update cart item quantity
- Auth: `customer` token

### `DELETE /api/cart/items/{id}`

- Purpose: remove a single cart item
- Auth: `customer` token

### `DELETE /api/cart/clear`

- Purpose: remove all active cart items
- Auth: `customer` token

### `POST /api/checkout`

- Purpose: validate cart, simulate payment, decrement stock, create order
- Auth: `customer` token

### `GET /api/orders`

- Purpose: list orders for the authenticated customer
- Auth: `customer` token

### `GET /api/orders/{id}`

- Purpose: return one order detail
- Auth: `customer` token

## Product Services

The three product services expose the same REST shape:

- `cloth-service` -> `/api/cloth-products`
- `laptop-service` -> `/api/laptop-products`
- `mobile-service` -> `/api/mobile-products`

### Public Endpoints

- `GET /api/<resource>`
- `GET /api/<resource>/{id}`

### Staff-Only Endpoints

- `POST /api/<resource>`
- `PUT /api/<resource>/{id}`
- `PATCH /api/<resource>/{id}`
- `DELETE /api/<resource>/{id}`

### Internal Endpoints

- `POST /api/internal/products/validate`
- `POST /api/internal/products/decrement-stock`

Example validation request:

```json
{
  "product_id": "uuid",
  "quantity": 2
}
```

Example validation response:

```json
{
  "exists": true,
  "sufficient_stock": true,
  "product": {
    "id": "uuid",
    "name": "Premium Hoodie",
    "price": "49.99",
    "stock": 12,
    "is_active": true
  }
}
```
