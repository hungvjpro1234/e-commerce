// Top categories by user interest
MATCH (:User)-[r:INTERESTED_IN]->(c:Category)
RETURN c.name AS category, SUM(r.score) AS total_interest
ORDER BY total_interest DESC
LIMIT 10;

// Most purchased products
MATCH (u:User)-[:PERFORMED]->(b:Behavior {behavior_type: 'purchase'})-[:ON_PRODUCT]->(p:Product)
RETURN p.name AS product, COUNT(*) AS purchase_count
ORDER BY purchase_count DESC
LIMIT 10;

// Search-to-purchase path for one user
MATCH (u:User {user_id: $user_id})-[:PERFORMED]->(b:Behavior)
RETURN b.session_id, b.behavior_type, b.timestamp, b.search_keyword
ORDER BY b.timestamp ASC;

// Products linked to a category
MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category})
RETURN p.name, p.price, p.stock
ORDER BY p.name ASC
LIMIT 20;

// Users interested in the same category as a product
MATCH (p:Product {product_id: $product_id})-[:BELONGS_TO]->(c:Category)<-[r:INTERESTED_IN]-(u:User)
RETURN c.name AS category, u.user_id AS user_id, r.score AS score
ORDER BY score DESC
LIMIT 20;
