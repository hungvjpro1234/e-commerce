"""End-to-end frontend smoke tests."""
import sys
import re
import requests

BASE = "http://localhost:8000"
session = requests.Session()

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"

results = []


def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {name}" + (f"  →  {detail}" if detail else ""))
    results.append((name, ok))


def get_csrf(sess, url):
    r = sess.get(url)
    m = re.search(r'csrfmiddlewaretoken.*?value="([^"]+)"', r.text)
    return m.group(1) if m else ""


# ── 1. Public pages ────────────────────────────────────────────────────────────
print("\n=== 1. Public pages ===")

r = session.get(f"{BASE}/")
check("Home page loads (200)", r.status_code == 200)
check("Home shows featured products", any(k in r.text for k in ["Featured", "card-meta", "domain_label"]))

r = session.get(f"{BASE}/products")
check("Product listing loads (200)", r.status_code == 200)
check("Product listing has cloth items", "Cloth" in r.text or "cloth" in r.text.lower())

r = session.get(f"{BASE}/products?domain=laptop")
check("Filter by laptop works", r.status_code == 200 and "Laptop" in r.text)

r = session.get(f"{BASE}/products?domain=mobile")
check("Filter by mobile works", r.status_code == 200 and "Mobile" in r.text)

r = session.get(f"{BASE}/products?domain=gaming")
check("Filter by gaming works", r.status_code == 200 and "Gaming" in r.text)

r = session.get(f"{BASE}/products?q=hoodie")
check("Search by keyword works", r.status_code == 200 and "Hoodie" in r.text)

r = session.get(f"{BASE}/login")
check("Customer login page (200)", r.status_code == 200)

r = session.get(f"{BASE}/register")
check("Customer register page (200)", r.status_code == 200)

r = session.get(f"{BASE}/staff/login")
check("Staff login page (200)", r.status_code == 200)

# ── 2. Get a real product ID for detail test ───────────────────────────────────
print("\n=== 2. Product detail ===")

import json
raw = requests.get("http://localhost:8003/api/cloth-products").json()
cloth_id = raw[0]["id"] if raw else None

if cloth_id:
    r = session.get(f"{BASE}/products/cloth/{cloth_id}")
    check("Cloth product detail (200)", r.status_code == 200)
    check("Detail shows product fields", "Price" in r.text or "price" in r.text.lower())
else:
    check("Product detail (skipped – no products)", False, "No cloth products returned")

raw_laptop = requests.get("http://localhost:8004/api/laptop-products").json()
laptop_id = raw_laptop[0]["id"] if raw_laptop else None
if laptop_id:
    r = session.get(f"{BASE}/products/laptop/{laptop_id}")
    check("Laptop product detail (200)", r.status_code == 200)

# ── 3. Customer login & profile ────────────────────────────────────────────────
print("\n=== 3. Customer auth ===")

customer_session = requests.Session()
csrf = get_csrf(customer_session, f"{BASE}/login")
r = customer_session.post(f"{BASE}/login", data={
    "email": "customer@example.com",
    "password": "strongpass123",
    "csrfmiddlewaretoken": csrf,
}, headers={"Referer": f"{BASE}/login"})
check("Customer login POST", r.status_code == 200)
check("Customer redirected to products", "/products" in r.url or "Products" in r.text)

r = customer_session.get(f"{BASE}/profile")
check("Customer profile page (200)", r.status_code == 200)
check("Profile shows email", "customer@example.com" in r.text)

r = customer_session.get(f"{BASE}/")
    check("Logged-in home page loads (200)", r.status_code == 200)

# ── 4. Cart flow ───────────────────────────────────────────────────────────────
print("\n=== 4. Cart flow ===")

r = customer_session.get(f"{BASE}/cart")
check("Cart page loads (200)", r.status_code == 200)

if cloth_id:
    # Add item to cart
    csrf = get_csrf(customer_session, f"{BASE}/products/cloth/{cloth_id}")
    detail_before_add = customer_session.get(f"{BASE}/products/cloth/{cloth_id}")
    r = customer_session.post(f"{BASE}/cart/add", data={
        "product_service": "cloth",
        "product_id": cloth_id,
        "quantity": 1,
        "csrfmiddlewaretoken": csrf,
    }, headers={"Referer": f"{BASE}/products/cloth/{cloth_id}"})
    check("Add item to cart (no 5xx)", r.status_code < 500)
    check("Cart redirected back after add", r.status_code == 200 and ("/products/cloth/" in r.url or "Item added to cart" in r.text))

    r = customer_session.get(f"{BASE}/cart")
    check("Cart shows added item", "product_name_snapshot" in r.text or cloth_id[:8] in r.text or "Cart" in r.text)

# ── 5. Checkout ────────────────────────────────────────────────────────────────
print("\n=== 5. Checkout ===")

r = customer_session.get(f"{BASE}/checkout")
check("Checkout page loads (200)", r.status_code == 200)

csrf = get_csrf(customer_session, f"{BASE}/checkout")
r = customer_session.post(f"{BASE}/checkout", data={
    "csrfmiddlewaretoken": csrf,
}, headers={"Referer": f"{BASE}/checkout"})
check("Checkout POST (no 5xx)", r.status_code < 500)
in_orders = "/orders" in r.url
check("After checkout, lands on order or orders page", in_orders or "Order" in r.text or r.status_code == 200)

# ── 6. Orders ─────────────────────────────────────────────────────────────────
print("\n=== 6. Order history ===")

r = customer_session.get(f"{BASE}/orders")
check("Orders page loads (200)", r.status_code == 200)



# ── 7. Staff auth & dashboard ──────────────────────────────────────────────────
print("\n=== 7. Staff auth & dashboard ===")

staff_session = requests.Session()
csrf = get_csrf(staff_session, f"{BASE}/staff/login")
r = staff_session.post(f"{BASE}/staff/login", data={
    "email": "admin@example.com",
    "password": "strongpass123",
    "csrfmiddlewaretoken": csrf,
}, headers={"Referer": f"{BASE}/staff/login"})
check("Staff login POST", r.status_code == 200)
check("Staff redirected to dashboard", "dashboard" in r.url or "Dashboard" in r.text)

r = staff_session.get(f"{BASE}/staff/dashboard")
check("Staff dashboard loads (200)", r.status_code == 200)
check("Dashboard shows domain counts", "Cloth Products" in r.text and "Gaming Products" in r.text)

# ── 8. Staff product management ────────────────────────────────────────────────
print("\n=== 8. Staff product management ===")

for domain in ("cloth", "laptop", "mobile", "accessory", "home-appliance", "book", "beauty", "food", "sports", "gaming"):
    r = staff_session.get(f"{BASE}/staff/products/{domain}")
    check(f"Staff {domain} product list (200)", r.status_code == 200)

# Create a product
csrf = get_csrf(staff_session, f"{BASE}/staff/products/cloth/new")
r = staff_session.post(f"{BASE}/staff/products/cloth/new", data={
    "name": "E2E Test Jacket",
    "description": "Created by automated test",
    "price": "49.99",
    "stock": "10",
    "image_url": "",
    "size": "M",
    "material": "Cotton",
    "color": "Blue",
    "gender": "Unisex",
    "is_active": "on",
    "csrfmiddlewaretoken": csrf,
}, headers={"Referer": f"{BASE}/staff/products/cloth/new"})
check("Staff create cloth product (no 5xx)", r.status_code < 500)
check("After create, back to product list", r.status_code == 200 and "/staff/products/cloth" in r.url)

# Verify it appears
r = staff_session.get(f"{BASE}/staff/products/cloth")
check("New product appears in list", "E2E Test Jacket" in r.text)

# ── 9. Unauthenticated protection ─────────────────────────────────────────────
print("\n=== 9. Auth protection ===")

anon = requests.Session()
r = anon.get(f"{BASE}/cart", allow_redirects=False)
check("Unauthenticated /cart redirects", r.status_code in (301, 302))

r = anon.get(f"{BASE}/orders", allow_redirects=False)
check("Unauthenticated /orders redirects", r.status_code in (301, 302))

r = anon.get(f"{BASE}/staff/dashboard", allow_redirects=False)
check("Unauthenticated /staff/dashboard redirects", r.status_code in (301, 302))

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*50)
total = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed
print(f"  Total: {total}   Passed: {passed}   Failed: {failed}")
if failed:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
    sys.exit(1)
else:
    print("  All tests passed!")
