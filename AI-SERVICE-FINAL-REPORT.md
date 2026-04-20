# 1. Trang bìa

**Tên môn / bài tập:** [Điền tên môn học]  
**Tên đề tài:** AI Service for E-Commerce Microservices (Behavior Modeling, Neo4j KB Graph, RAG Chat, Web Integration)  
**Họ tên sinh viên:** [Điền họ tên]  
**Lớp:** [Điền lớp]  
**Nhóm:** [Điền nhóm]  
**Giảng viên:** [Điền giảng viên]  
**Thời gian nộp:** [Điền thời gian nộp]

---

# 2. Mô tả AI Service

Đồ án đã triển khai AI layer trên nền hệ thống e-commerce microservices (Django/DRF) với 4 nhóm chức năng chính:

1. Sinh dữ liệu hành vi `data_user500.csv` với 500 users và 8 behaviors chuẩn.
2. Huấn luyện và so sánh 3 mô hình tuần tự (`RNN`, `LSTM`, `biLSTM`) cho bài toán dự đoán hành vi kế tiếp.
3. Xây dựng và nạp `KB_Graph` trên Neo4j từ dữ liệu hành vi + catalog sản phẩm.
4. Tích hợp AI vào luồng người dùng thực tế: recommendation ở search/cart và chat widget tùy biến trên web.

AI được gắn vào hệ thống hiện có theo kiến trúc service độc lập:
- `behavior-service`: nhận/ghi event từ `web-service` và `customer-service`.
- `recommendation-service`: inference từ `model_best.pt`, trả gợi ý sản phẩm.
- `chatbot-service`: truy vấn Neo4j và trả lời grounded kèm evidence.
- `web-service`: đóng vai trò BFF/UI, gọi recommendation/chatbot API và render kết quả.

---

# 3. Kiến trúc tổng thể hệ thống

## 3.1. Thành phần chính

Hệ thống chạy bằng Docker Compose, bao gồm:
- Front/BFF: `web-service`.
- Domain services: `customer-service`, `staff-service`, `cloth-service`, `laptop-service`, `mobile-service`, `accessory-service`, `home-appliance-service`, `book-service`, `beauty-service`, `food-service`, `sports-service`, `gaming-service`.
- AI services: `behavior-service`, `recommendation-service`, `chatbot-service`.
- Graph DB: `neo4j`.
- Mỗi service backend có DB riêng (PostgreSQL), riêng `web-service` dùng SQLite local.

```yaml
services:
  behavior-service:
    ports:
      - "${BEHAVIOR_SERVICE_PORT:-8014}:8000"
  recommendation-service:
    ports:
      - "${RECOMMENDATION_SERVICE_PORT:-8015}:8000"
  chatbot-service:
    ports:
      - "${CHATBOT_SERVICE_PORT:-8006}:8000"
    depends_on:
      - chatbot-db
      - neo4j
  neo4j:
    image: neo4j:5.20
    ports:
      - "7474:7474"
      - "7687:7687"
```
Nguồn: `docker-compose.yml`

## 3.2. Luồng dữ liệu AI trong runtime

1. User thao tác ở web (search, view, cart, checkout).
2. `web-service`/`customer-service` phát sự kiện sang `behavior-service` qua `POST /api/internal/events`.
3. `recommendation-service` dùng chuỗi event gần nhất để dự đoán next behavior và lấy candidate products từ product services.
4. `chatbot-service` truy vấn Neo4j (`/db/{database}/tx/commit`) để lấy context và tạo câu trả lời grounded.
5. `web-service` hiển thị block recommendation + chat widget tùy biến.

```python
def emit_behavior_event(...):
    response = requests.post(
        f"{settings.BEHAVIOR_SERVICE_URL}/api/internal/events",
        json=payload,
        headers={
            "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
            "X-Service-Name": settings.SERVICE_NAME,
        },
        timeout=5,
    )
```
Nguồn: `services/customer-service/apps/behavior_tracking.py`

## 3.3. Endpoint chính

- Behavior:
  - `POST /api/internal/events`
  - `GET /api/events`
  - `GET /api/events/export`
- Recommendation:
  - `POST /api/recommend/predict-next-behavior`
  - `POST /api/recommend/products`
- Chatbot:
  - `POST /api/chat`
  - `POST /api/chat/context`
- Web proxy:
  - `POST /chat/context`
  - `POST /chat/message`

```python
urlpatterns = [
    path("internal/events", BehaviorEventIngestAPIView.as_view()),
    path("events", BehaviorEventListAPIView.as_view()),
    path("events/export", BehaviorEventExportAPIView.as_view()),
]
```
Nguồn: `services/behavior-service/apps/events/urls.py`

```python
urlpatterns = [
    path("chat/context", views.ChatContextProxyView.as_view(), name="chat_context_proxy"),
    path("chat/message", views.ChatMessageProxyView.as_view(), name="chat_message_proxy"),
]
```
Nguồn: `services/web-service/apps/customer_portal/urls.py`

---

# 4. Mô tả dữ liệu `data_user500.csv`

## 4.1. Nguồn gốc và cách sinh dữ liệu

Dataset được tạo bởi script `generate_data_user500.py` theo chiến lược hybrid:
- đọc catalog sản phẩm thật từ seed files của product services,
- cho phép trộn real events nếu có,
- sinh synthetic sessions để đảm bảo đủ 500 users và đầy đủ 8 behavior types.

```python
BEHAVIOR_TYPES = (
    "register",
    "login",
    "search",
    "view_product",
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "purchase",
)

CSV_FIELDS = [
    "user_id", "session_id", "timestamp", "behavior_type",
    "product_service", "product_id", "category", "search_keyword",
    "quantity", "step_in_session", "label_next_behavior",
    "source_service", "is_synthetic",
]
```
Nguồn: `services/recommendation-service/scripts/generate_data_user500.py`

## 4.2. Ý nghĩa cột và label

- `user_id`, `session_id`, `timestamp`: khóa định danh và thứ tự thời gian.
- `behavior_type`: hành vi hiện tại (1 trong 8 lớp).
- `product_service`, `product_id`, `category`, `search_keyword`, `quantity`: đặc trưng ngữ cảnh.
- `step_in_session`: vị trí event trong session.
- `label_next_behavior`: nhãn supervised để dự đoán bước kế tiếp.
- `source_service`: nguồn phát sinh event (`web-service` hoặc `customer-service`).
- `is_synthetic`: cờ synthetic/real.

## 4.3. 8 behaviors sử dụng

`register`, `login`, `search`, `view_product`, `add_to_cart`, `update_cart_quantity`, `remove_from_cart`, `purchase`.

Bộ hành vi này bám đúng flow e-commerce thực tế trong codebase (auth, search, product detail, cart, checkout).

## 4.4. 20 dòng dữ liệu mẫu

```csv
user_id,session_id,timestamp,behavior_type,product_service,product_id,category,search_keyword,quantity,step_in_session,label_next_behavior,source_service,is_synthetic
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:06:00+00:00,register,,,,,,1,login,customer-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:14:00+00:00,login,,,,,,2,search,customer-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:20:00+00:00,search,,,Food & Drinks,snack,,3,view_product,web-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:31:00+00:00,view_product,food,72fc5eec-b954-5b32-b13c-ba9f26f16be1,Food & Drinks,,,4,add_to_cart,web-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:39:00+00:00,add_to_cart,food,72fc5eec-b954-5b32-b13c-ba9f26f16be1,Food & Drinks,,1,5,update_cart_quantity,customer-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:44:00+00:00,update_cart_quantity,food,72fc5eec-b954-5b32-b13c-ba9f26f16be1,Food & Drinks,,1,6,purchase,customer-service,1
ed268ee2-0ea6-5eb0-bc5d-3867931d51e9,2c7e3b9e-9e1f-50b0-8987-6a5269bb6f42,2026-01-01T18:49:00+00:00,purchase,food,72fc5eec-b954-5b32-b13c-ba9f26f16be1,Food & Drinks,,2,7,,customer-service,1
321eb181-03f5-50c9-bb48-888d34319d6e,17ee3246-1126-5b68-8ad0-4fa5860288ce,2026-01-01T19:11:00+00:00,login,,,,,,1,search,customer-service,1
321eb181-03f5-50c9-bb48-888d34319d6e,17ee3246-1126-5b68-8ad0-4fa5860288ce,2026-01-01T19:16:00+00:00,search,,,Home Appliances,blender,,2,view_product,web-service,1
321eb181-03f5-50c9-bb48-888d34319d6e,17ee3246-1126-5b68-8ad0-4fa5860288ce,2026-01-01T19:23:00+00:00,view_product,home-appliance,b22fe093-1c52-56ba-9a0b-52046845c96f,Home Appliances,,,3,,web-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:11:00+00:00,login,,,,,,1,search,customer-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:17:00+00:00,search,,,Laptop,samsung,,2,view_product,web-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:25:00+00:00,view_product,laptop,20618e51-7524-55f1-8943-d19d732f7e91,Laptop,,,3,view_product,web-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:33:00+00:00,view_product,laptop,20618e51-7524-55f1-8943-d19d732f7e91,Laptop,,,4,add_to_cart,web-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:39:00+00:00,add_to_cart,laptop,20618e51-7524-55f1-8943-d19d732f7e91,Laptop,,1,5,purchase,customer-service,1
6a5f199a-bd14-56e2-a2e2-52d5641fa422,a2912c34-a6fc-59ab-abe5-c907e7436b8e,2026-01-01T20:48:00+00:00,purchase,laptop,20618e51-7524-55f1-8943-d19d732f7e91,Laptop,,3,6,,customer-service,1
6b0bf5b5-2023-531f-a9e4-61703d9408e6,da336920-97c2-5994-9c84-3006900d970f,2026-01-01T22:10:00+00:00,register,,,,,,1,login,customer-service,1
6b0bf5b5-2023-531f-a9e4-61703d9408e6,da336920-97c2-5994-9c84-3006900d970f,2026-01-01T22:16:00+00:00,login,,,,,,2,search,customer-service,1
6b0bf5b5-2023-531f-a9e4-61703d9408e6,da336920-97c2-5994-9c84-3006900d970f,2026-01-01T22:20:00+00:00,search,,,Home Appliances,rice cooker,,3,view_product,web-service,1
6b0bf5b5-2023-531f-a9e4-61703d9408e6,da336920-97c2-5994-9c84-3006900d970f,2026-01-01T22:23:00+00:00,view_product,home-appliance,a9ae89e7-becb-53f4-8a03-fd576261865d,Home Appliances,,,4,add_to_cart,web-service,1
```
Nguồn: `docs/sample-data/data_user500.csv`

---

# 5. Câu 2a — Mô hình RNN, LSTM, biLSTM

## 5.1. Bài toán học máy

Bài toán đã triển khai là **next behavior prediction** (multi-class classification, 8 classes).

- **Input:** chuỗi event gần nhất của user/session (behavior + category + product_service + source_service + quantity).
- **Output:** nhãn hành vi kế tiếp (`label_next_behavior`).

## 5.2. Tiền xử lý dữ liệu

Pipeline preprocessing thực hiện:
- chuẩn hóa encoder cho behavior/category/product_service/source_service,
- padding sequence length cố định (mặc định 5),
- chia train/val/test theo user-level split (70/15/15),
- ghi artifact: `train.jsonl`, `val.jsonl`, `test.jsonl`, `encoders.json`, `summary.json`.

```python
def create_samples(rows, sequence_length, seed):
    behavior_encoder = build_encoder((row["behavior_type"] for row in rows))
    label_encoder = build_label_encoder()
    category_encoder = build_encoder((row["category"] for row in rows), include_unknown=True)
    ...
    split_map = split_users({row["user_id"] for row in rows}, seed=seed)
    ...
    "target_behavior_id": label_encoder[label],
    "input_behavior_ids": build_sequence(...),
```
Nguồn: `services/recommendation-service/scripts/preprocess_behavior_sequences.py`

## 5.3. Kiến trúc 3 mô hình

Mã nguồn dùng chung một lớp `SequenceBehaviorModel`, đổi `model_type` để tạo `rnn`, `lstm`, `bilstm`.

```python
recurrent_cls = {
    "rnn": nn.RNN,
    "lstm": nn.LSTM,
    "bilstm": nn.LSTM,
}[model_type]
bidirectional = model_type == "bilstm"
self.recurrent = recurrent_cls(
    input_size=input_size,
    hidden_size=hidden_size,
    batch_first=True,
    bidirectional=bidirectional,
)
```
Nguồn: `services/recommendation-service/apps/recommendations/ml.py`

## 5.4. Huấn luyện mô hình

Hyperparameters có trong code:
- epochs: 14
- batch size: 64
- learning rate: 0.002
- hidden size: 64
- embedding dim: 16
- dropout: 0.2
- optimizer: Adam
- loss: CrossEntropyLoss

```python
parser.add_argument("--epochs", type=int, default=14)
parser.add_argument("--batch-size", type=int, default=64)
parser.add_argument("--learning-rate", type=float, default=0.002)
...
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
```
Nguồn: `services/recommendation-service/scripts/train_behavior_models.py`

## 5.5. Kết quả đánh giá

Kết quả dưới đây lấy trực tiếp từ `model_comparison.json` và `training_report.json`.

| Model | Accuracy | Weighted F1 | Macro F1 | Best Epoch |
|---|---:|---:|---:|---:|
| RNN | 0.8974 | 0.8931 | 0.7871 | 4 |
| LSTM | 0.9015 | 0.8956 | 0.7889 | 7 |
| biLSTM | **0.9042** | **0.8982** | **0.7925** | 2 |

`model_best` được chọn là `biLSTM` theo rule: `highest weighted_f1, then accuracy`.

```json
{
  "best_model": {
    "name": "bilstm",
    "selection_rule": "highest weighted_f1, then accuracy",
    "artifact": "services\\recommendation-service\\artifacts\\trained_models\\model_best.pt"
  }
}
```
Nguồn: `services/recommendation-service/artifacts/trained_models/training_report.json`

## 5.6. Plots và visualization

Ảnh chart không được nhúng giả vào báo cáo này. Cách tái hiện để tự chụp:

### Cách tái hiện để chụp màn hình

1. Chạy train:
```bash
python services/recommendation-service/scripts/train_behavior_models.py \
  --preprocessed-dir services/recommendation-service/artifacts/preprocessed \
  --output-dir services/recommendation-service/artifacts/trained_models
```
Nguồn: `services/recommendation-service/scripts/train_behavior_models.py`

2. Mở file output để chụp:
- `services/recommendation-service/artifacts/trained_models/model_comparison.png`
- `services/recommendation-service/artifacts/trained_models/plots_rnn/training_curves.png`
- `services/recommendation-service/artifacts/trained_models/plots_lstm/training_curves.png`
- `services/recommendation-service/artifacts/trained_models/plots_bilstm/training_curves.png`

3. Chụp thêm bảng số liệu:
- `services/recommendation-service/artifacts/trained_models/model_comparison.json`
- `services/recommendation-service/artifacts/trained_models/training_report.json`

---

# 6. Câu 2b — KB_Graph với Neo4j

## 6.1. Mô hình graph

Graph có 4 node chính và các quan hệ:
- `(:User)`
- `(:Behavior)`
- `(:Product)`
- `(:Category)`

Quan hệ:
- `(:User)-[:PERFORMED]->(:Behavior)`
- `(:Behavior)-[:ON_PRODUCT]->(:Product)`
- `(:Behavior)-[:IN_CATEGORY]->(:Category)`
- `(:Product)-[:BELONGS_TO]->(:Category)`
- `(:User)-[:INTERESTED_IN]->(:Category)`

```python
statements = [
    "CREATE CONSTRAINT user_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
    "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT product_product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
    "CREATE CONSTRAINT behavior_behavior_id IF NOT EXISTS FOR (b:Behavior) REQUIRE b.behavior_id IS UNIQUE",
]
```
Nguồn: `services/chatbot-service/scripts/import_kb_graph.py`

## 6.2. Cách xây dựng graph từ dữ liệu

Pipeline import:
1. Đọc `data_user500.csv`.
2. Build graph documents (`users`, `categories`, `products`, `behaviors`, `interests`).
3. Kết nối Neo4j HTTP transactional endpoint.
4. Tạo constraints + `UNWIND` để `MERGE` nodes/relationships.
5. Verify graph counts và ghi summary JSON.

```python
rows = load_behavior_rows(args.dataset)
product_catalog = fetch_product_catalog()
documents = build_graph_documents(rows, product_catalog)
...
create_constraints(client)
import_documents(client, documents)
verified_counts = verify_graph_counts(client)
summary = write_summary(Path(args.summary_output), documents, synced, verified_counts=verified_counts)
```
Nguồn: `services/chatbot-service/scripts/import_kb_graph.py`

## 6.3. Code / query tiêu biểu

```cypher
MATCH (:User)-[r:INTERESTED_IN]->(c:Category)
RETURN c.name AS category, SUM(r.score) AS total_interest
ORDER BY total_interest DESC
LIMIT 10;

MATCH (u:User)-[:PERFORMED]->(b:Behavior {behavior_type: 'purchase'})-[:ON_PRODUCT]->(p:Product)
RETURN p.name AS product, COUNT(*) AS purchase_count
ORDER BY purchase_count DESC
LIMIT 10;
```
Nguồn: `docs/sample-data/kb_graph_queries.cypher`

Graph import summary hiện có:
- users: 500
- categories: 10
- products: 94
- behaviors: 6119
- performed: 6119
- on_product: 3441
- in_category: 4630
- interested_in: 1115
- belongs_to: 94

```json
{
  "synced_to_neo4j": true,
  "node_counts": {
    "users": 500,
    "categories": 10,
    "products": 94,
    "behaviors": 6119
  }
}
```
Nguồn: `services/chatbot-service/artifacts/kb_graph_import_summary.json`

## 6.4. Cách mở graph để tự screenshot

### Cách tái hiện để chụp màn hình

1. Khởi động stack:
```bash
docker compose up -d
```
Nguồn: `docker-compose.yml`

2. Mở Neo4j Browser:
- URL: `http://localhost:7474`
- Credentials: lấy từ `.env` (`NEO4J_USERNAME`, `NEO4J_PASSWORD`)

3. Query nên chạy để hiện graph:
```cypher
MATCH (u:User)-[:PERFORMED]->(b:Behavior)-[:ON_PRODUCT]->(p:Product)-[:BELONGS_TO]->(c:Category)
RETURN u,b,p,c
LIMIT 50;
```

4. Query thống kê để chụp bảng:
```cypher
MATCH (n) RETURN labels(n) AS labels, count(*) AS total;
```

5. Query mẫu có sẵn:
- `docs/sample-data/kb_graph_queries.cypher`

---

# 7. Câu 2c — RAG và Chat dựa trên KB_Graph

## 7.1. Kiến trúc chatbot

`chatbot-service` gồm:
- `Neo4jHttpClient`: gửi Cypher qua HTTP transactional API.
- `GraphRetriever`: xác định intent và lấy records/evidence từ Neo4j.
- `GroundedAnswerService`: dựng câu trả lời dựa trên records.
- `ChatbotService`: orchestration cho `/api/chat` và `/api/chat/context`.

```python
class ChatbotService:
    def chat(self, *, message, context, debug=False):
        retrieval = self.retriever.retrieve(message=message, context=context)
        answer = self.answer_service.build_answer(message=message, retrieval_result=retrieval)
        payload = {
            "answer": answer,
            "evidence": retrieval["evidence"],
            "context_summary": {
                "intent": retrieval["intent"],
                "domain": retrieval["domain"],
                "record_count": len(retrieval["records"]),
            },
        }
```
Nguồn: `services/chatbot-service/apps/chat/services.py`

## 7.2. Luồng truy vấn RAG

Luồng truy vấn thực tế:
1. Nhận `message` + `context`.
2. Suy luận intent (`product_discovery`, `similar_item`, `cart_suggestion`, ...).
3. Query Neo4j theo intent.
4. Tạo `evidence` list (product/category IDs + title).
5. Sinh câu trả lời grounded từ evidence.
6. Trả về `answer`, `evidence`, `context_summary`, optional `debug.query_trace`.

```python
if product_id:
    records = self._query_similar_products(product_id)
    evidence = [{"type": "product", "id": row[1], "title": row[2], "domain": row[5], "category": row[0]} for row in records]
    return {"intent": intent, "domain": domain, "records": records, "evidence": evidence, "query_trace": ["similar_products_by_category"]}
```
Nguồn: `services/chatbot-service/apps/chat/services.py`

## 7.3. API chat

```python
class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = get_chatbot_service().chat(
            message=payload["message"],
            context=payload.get("context", {}),
            debug=payload.get("debug", False),
        )
        return ok(result, "Chat response generated.")
```
Nguồn: `services/chatbot-service/apps/chat/views.py`

```python
urlpatterns = [
    path("api/", include("apps.chat.urls")),
]
```
Nguồn: `services/chatbot-service/config/urls.py`

## 7.4. Code tiêu biểu

```python
class Neo4jHttpClient:
    def run(self, statement, parameters=None):
        response = self.session.post(
            f"{self.base_url}/db/{settings.NEO4J_DATABASE}/tx/commit",
            json={"statements": [{"statement": statement, "parameters": parameters or {}}]},
            timeout=12,
        )
        ...
```
Nguồn: `services/chatbot-service/apps/chat/services.py`

## 7.5. Cách tự chạy để chụp màn hình chat

### Cách tái hiện để chụp màn hình

1. Chạy services:
```bash
docker compose up -d
```

2. Mở UI:
- `http://localhost:8000/products`
- bấm nút chat FAB góc phải dưới.

3. Prompt nên dùng để ra evidence đẹp:
- `Show me similar items` (ở trang product detail có `product_id` context)
- `What should I add with these cart items?` (ở cart page)
- `Recommend products like my search` (ở search page)

4. Nếu test bằng API:
```bash
curl -X POST http://localhost:8006/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me similar items","context":{"domain":"cloth","product_id":"<product_id>"},"debug":true}'
```

5. Chụp màn hình cần có:
- text `answer`
- mảng `evidence`
- `context_summary.intent`

---

# 8. Câu 2d — Tích hợp vào hệ e-commerce

## 8.1. Tích hợp recommendation ở search

Tại `ProductListView`:
- khi có search query, hệ thống emit event `search`,
- cập nhật recent events trong session,
- gọi `recommendation_gw.recommend_products(...)`,
- render block recommendation trong `products.html`.

```python
if search:
    ...
    emit_behavior_event(event_type="search", ...)
    push_recent_behavior_event(request, event_type="search", ...)
    recommendations = load_recommendations(
        request,
        recent_events=get_recent_behavior_events(request),
        search_keyword=search,
        category=domain_filter,
        product_service=domain_filter,
        limit=4,
    )
```
Nguồn: `services/web-service/apps/customer_portal/views.py`

## 8.2. Tích hợp recommendation ở giỏ hàng

Tại `CartView`:
- lấy cart data,
- dựng recent behavior payload (fallback từ cart items nếu cần),
- gọi recommendation service,
- render block “You may also like” trên `cart.html`.

```python
cart_items = cart_data.get("items", [])
recent_events = get_recommendation_payload(request, cart_items=cart_items)
recommendations = load_recommendations(
    request,
    recent_events=recent_events,
    category=cart_domain,
    product_service=cart_domain,
    product_id=cart_items[-1].get("product_id", "") if cart_items else "",
    limit=4,
)
```
Nguồn: `services/web-service/apps/customer_portal/views.py`

## 8.3. Tích hợp giao diện chat

Chat UI đã là widget tùy biến trong `base.html` (không dùng UI mặc định kiểu ChatGPT):
- FAB toggle,
- panel chat riêng,
- quick prompts theo page context,
- AJAX call `/chat/context` và `/chat/message`.

```html
<div id="chat-fab">
  <div id="chat-panel" aria-live="polite">...</div>
  <button id="chat-toggle" type="button" aria-label="Open chat">...</button>
</div>
<script>
  const response = await postJson("/chat/message", {
    message,
    context: chatContext,
    history,
  });
</script>
```
Nguồn: `services/web-service/templates/base.html`

## 8.4. Code tiêu biểu

```html
{% include 'customer_portal/partials/recommendation_block.html' with title='You may also like' subtitle='Suggestions tuned to your current search and recent browsing.' %}
```
Nguồn: `services/web-service/templates/customer_portal/products.html`

```html
{% include 'customer_portal/partials/recommendation_block.html' with title='You may also like' subtitle='Suggested additions based on what is already in your cart.' %}
```
Nguồn: `services/web-service/templates/customer_portal/cart.html`

```html
{% if recommendations and recommendations.products %}
<section class="panel recommendation-panel">
  ...
  <span class="badge">Next: {{ recommendations.predicted_behavior|cut:"_"|title }}</span>
  ...
</section>
{% endif %}
```
Nguồn: `services/web-service/templates/customer_portal/partials/recommendation_block.html`

## 8.5. Cách mở trang để tự screenshot

### Cách tái hiện để chụp màn hình

1. Chạy stack:
```bash
docker compose up -d
```

2. Trang search có recommendation:
- URL: `http://localhost:8000/products?q=hoodie&domain=cloth`
- Điều kiện: đăng nhập customer để có session behavior context.
- Chụp block “You may also like”.

3. Trang cart có recommendation:
- URL: `http://localhost:8000/cart`
- Điều kiện: thêm ít nhất 1 sản phẩm vào giỏ hàng.
- Chụp block recommendation + danh sách reason pills.

4. Trang product detail + chat:
- URL mẫu: `http://localhost:8000/products/cloth/<product_id>`
- Bấm chat FAB và nhập prompt “Show me similar items”.
- Chụp giao diện chat + citation tags.

---

# 9. Kết quả triển khai và nhận xét

## 9.1. Kết quả đạt được

- Đã có dataset `data_user500.csv` đúng scope 500 users và 8 behaviors.
- Đã có pipeline đầy đủ: generate -> preprocess -> train -> chọn best model -> inference API.
- Đã có `model_best.pt` và báo cáo metric lưu trong artifact JSON.
- Đã có Neo4j graph import script, query mẫu, và summary counts xác nhận graph đã được nạp.
- Đã có chatbot grounded theo evidence từ graph/product data.
- Đã có tích hợp web hoàn chỉnh cho recommendation (search/cart) và custom chat widget.

## 9.2. Ưu điểm

- Thiết kế microservice rõ trách nhiệm từng thành phần.
- Recommendation trả về explainability (`reason_codes`, `reason_summary`).
- Chatbot trả về bằng chứng (`evidence`) và trace (`query_trace`) giúp debug/đánh giá grounding.
- Có artifact đầy đủ phục vụ nộp bài (JSON, PNG, Cypher).

## 9.3. Hạn chế hiện tại (dựa trên code)

1. `web-service` hiện dùng SQLite local trong settings mặc định, trong khi các service khác dùng PostgreSQL.
2. Một số luồng test API dùng mock/service abstraction; để khẳng định toàn bộ E2E production-grade cần kiểm tra runtime liên service trong môi trường deploy ổn định lâu dài.
3. Chưa thấy healthcheck riêng trong compose cho các AI services (chỉ `depends_on` cơ bản).
4. Chưa đủ bằng chứng từ codebase để khẳng định có benchmark latency/throughput cho chatbot/recommendation dưới tải cao.

---

# 10. Kết luận

Đồ án đã hoàn thành đầy đủ các yêu cầu trọng tâm của đề bài:
- sinh `data_user500.csv` (500 users, 8 behaviors),
- huấn luyện và so sánh `RNN`, `LSTM`, `biLSTM`, chọn `model_best`,
- xây dựng `KB_Graph` trên Neo4j,
- triển khai chat dựa trên truy xuất tri thức từ graph,
- tích hợp AI trực tiếp vào trải nghiệm mua sắm (search/cart/chat UI tùy biến).

Giá trị AI trong hệ e-commerce thể hiện ở hai điểm chính:
1. cá nhân hóa gợi ý sản phẩm dựa trên hành vi gần nhất;
2. hỗ trợ hội thoại có căn cứ dữ liệu graph, tăng khả năng giải thích và tính tin cậy.

---

# 11. Phụ lục mã nguồn trích dẫn

- `docker-compose.yml` — cấu hình tích hợp toàn bộ service + Neo4j + DB.
- `services/recommendation-service/scripts/generate_data_user500.py` — sinh dataset 500 users + 8 behaviors.
- `services/recommendation-service/scripts/preprocess_behavior_sequences.py` — tạo sequence và split train/val/test.
- `services/recommendation-service/scripts/train_behavior_models.py` — huấn luyện, đánh giá, xuất artifacts, chọn best model.
- `services/recommendation-service/apps/recommendations/ml.py` — định nghĩa kiến trúc RNN/LSTM/biLSTM.
- `services/recommendation-service/apps/recommendations/services.py` — inference + scoring recommendation.
- `services/recommendation-service/apps/recommendations/views.py` — API prediction/recommendation.
- `services/recommendation-service/config/urls.py` — route recommendation APIs.
- `services/recommendation-service/artifacts/trained_models/model_comparison.json` — bảng so sánh 3 mô hình.
- `services/recommendation-service/artifacts/trained_models/training_report.json` — báo cáo huấn luyện và best model.
- `services/recommendation-service/artifacts/preprocessed/summary.json` — thống kê preprocess.
- `docs/sample-data/data_user500.csv` — dữ liệu mẫu phục vụ huấn luyện.
- `services/chatbot-service/scripts/import_kb_graph.py` — pipeline import graph vào Neo4j.
- `docs/sample-data/kb_graph_queries.cypher` — query mẫu cho screenshot/report.
- `services/chatbot-service/artifacts/kb_graph_import_summary.json` — summary số lượng node/relationship.
- `services/chatbot-service/apps/chat/services.py` — retrieval + grounded answer.
- `services/chatbot-service/apps/chat/views.py` — chat APIs.
- `services/chatbot-service/config/urls.py` — route chatbot API.
- `services/chatbot-service/config/settings/base.py` — cấu hình kết nối Neo4j.
- `services/behavior-service/apps/events/urls.py` — ingest/list/export events.
- `services/customer-service/apps/behavior_tracking.py` — phát sự kiện hành vi sang behavior-service.
- `services/web-service/apps/customer_portal/views.py` — tích hợp recommendation/chat vào flow web.
- `services/web-service/apps/customer_portal/urls.py` — route search/cart/chat proxy.
- `services/web-service/apps/gateway/clients.py` — gateway gọi recommendation/chatbot/product/customer services.
- `services/web-service/templates/base.html` — custom chat widget UI.
- `services/web-service/templates/customer_portal/products.html` — recommendation block ở search page.
- `services/web-service/templates/customer_portal/cart.html` — recommendation block ở cart page.
- `services/web-service/templates/customer_portal/partials/recommendation_block.html` — component hiển thị recommendation.
- `services/web-service/config/settings/base.py` — cấu hình URL nội bộ các service.
