# Báo cáo: Xây dựng Ứng dụng "Phân tích Hành vi Khách hàng để Tư vấn Dịch vụ"

**Môn học:** Thương mại Điện tử  
**Nhóm thực hiện:** Nhóm phát triển Hệ thống E-Commerce  
**Ngày hoàn thành:** Tháng 4 năm 2026

---

## Tóm tắt

Báo cáo này trình bày quá trình thiết kế và triển khai ứng dụng trí tuệ nhân tạo phục vụ tư vấn khách hàng tự động trong hệ thống thương mại điện tử đa dịch vụ. Hệ thống được xây dựng theo kiến trúc microservices, tích hợp ba thành phần AI chính: mô hình phân tích hành vi khách hàng (thiết kế), cơ sở tri thức (Knowledge Base) động, và chatbot tư vấn dựa trên kỹ thuật Retrieval-Augmented Generation (RAG). Trong phạm vi iteration này, module `chatbot-service` được triển khai đầy đủ và tích hợp với các dịch vụ danh mục sản phẩm hiện có, trong khi `behavior-service` và `recommendation-service` ở giai đoạn thiết kế chuẩn bị cho vòng phát triển tiếp theo.

---

## 1. Mô hình Phân tích Hành vi Khách hàng (Behavior Model)

### 1.1 Định nghĩa bài toán

Phân tích hành vi khách hàng trong hệ thống e-commerce là bài toán thu thập và diễn giải các hành động mà khách hàng thực hiện trên nền tảng. Cụ thể, hệ thống theo dõi ba loại sự kiện chính:

- **Xem sản phẩm (view):** Khách hàng mở trang chi tiết sản phẩm.
- **Thêm vào giỏ hàng (cart\_add):** Khách hàng gọi `POST /api/cart/items`.
- **Mua hàng (purchase):** Đơn hàng hoàn tất thành công.

Từ những mẫu hành vi này, hệ thống có thể dự đoán sản phẩm mà một khách hàng cụ thể có xu hướng quan tâm và chủ động đề xuất các sản phẩm phù hợp.

### 1.2 Giá trị kinh doanh

| Trường hợp sử dụng | Giá trị mang lại |
|---|---|
| Gợi ý sản phẩm cá nhân hóa | Tăng tỷ lệ chuyển đổi |
| Sản phẩm liên quan trên trang chi tiết | Tăng giá trị đơn hàng trung bình |
| Chatbot hiểu catalog | Giảm tải bộ phận hỗ trợ, khám phá sản phẩm nhanh hơn |
| Phân khúc khách hàng | Marketing mục tiêu |

### 1.3 Schema dữ liệu hành vi

Dữ liệu hành vi được lưu trữ trong `behavior-service` với lược đồ cơ sở dữ liệu như sau:

```sql
CREATE TABLE behavior_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    product_id      UUID NOT NULL,
    product_service VARCHAR(32) NOT NULL,  -- 'cloth', 'laptop', 'mobile'
    event_type      VARCHAR(32) NOT NULL,  -- 'view', 'cart_add', 'purchase'
    quantity        INTEGER DEFAULT 1,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_behavior_user    ON behavior_events(user_id);
CREATE INDEX idx_behavior_product ON behavior_events(product_id, product_service);
CREATE INDEX idx_behavior_type    ON behavior_events(event_type, created_at);
```

### 1.4 Thiết kế mô hình Deep Learning

#### 1.4.1 Collaborative Filtering bằng Matrix Factorization

Phương pháp đơn giản và hiệu quả phù hợp với quy mô hệ thống:

1. Xây dựng ma trận user-item: hàng = người dùng, cột = sản phẩm, giá trị = điểm tương tác có trọng số (`purchase=3`, `cart_add=2`, `view=1`).
2. Phân rã ma trận bằng Truncated SVD (thư viện `scikit-learn`):

   ```
   U, S, Vt = TruncatedSVD(n_components=50).fit_transform(matrix)
   ```

3. Dự đoán điểm: `predicted = U @ diag(S) @ Vt`
4. Với một người dùng cho trước, sắp xếp cột theo điểm dự đoán và trả về top-N sản phẩm còn hàng.

**Xử lý Cold Start:** Với người dùng mới chưa có lịch sử, hệ thống trả về top sản phẩm phổ biến nhất theo tổng `purchase + cart_add` trong 30 ngày gần nhất.

#### 1.4.2 Mô hình Deep Learning mở rộng

**Embedding + Dense Network:**

```
Input: [user_embedding(128) | product_embedding(128)]
       → Dense(256, relu)
       → Dropout(0.3)
       → Dense(128, relu)
       → Dense(1, sigmoid)   ← xác suất tương tác dự đoán
```

**Sequential Model (dự đoán sản phẩm tiếp theo):**

```
Input: chuỗi hành vi (độ dài thay đổi, mỗi item = product embedding)
       → LSTM(128)
       → Dense(n_products, softmax)   ← phân phối xác suất trên toàn bộ sản phẩm
```

#### 1.4.3 Quy trình huấn luyện

```
1. Export bảng behavior_events ra CSV hoặc Parquet
2. Huấn luyện mô hình offline (Jupyter Notebook hoặc training script)
3. Serialize mô hình: joblib.dump(model, 'model.pkl')
4. Load mô hình vào recommendation-service khi khởi động
5. Expose GET /recommendations/{user_id} → chạy inference, trả về JSON
6. Tái huấn luyện định kỳ (cron hàng ngày hoặc trigger thủ công)
```

#### 1.4.4 Định dạng đầu vào/đầu ra mô hình

**Đầu vào:**

```python
{
    "user_id": "uuid",
    "history": [
        {"product_id": "uuid", "product_service": "laptop",
         "event_type": "view", "timestamp": 1714000000},
        {"product_id": "uuid", "product_service": "laptop",
         "event_type": "cart_add", "timestamp": 1714001000},
    ]
}
```

**Đầu ra:**

```python
{
    "recommendations": [
        {"product_id": "uuid", "product_service": "laptop", "score": 0.92},
        {"product_id": "uuid", "product_service": "mobile", "score": 0.81},
    ]
}
```

### 1.5 Các use-case được hỗ trợ

| Use-case | Mô tả | Trạng thái |
|---|---|---|
| Gợi ý sản phẩm cá nhân | Top-N sản phẩm cho user\_id | Thiết kế — giai đoạn tới |
| Trang chủ cá nhân hóa | Carousel sản phẩm được cá nhân hóa | Thiết kế — giai đoạn tới |
| Sản phẩm liên quan | Item-based collaborative filtering | Thiết kế — giai đoạn tới |
| Dự đoán mua hàng tiếp theo | LSTM hoặc Markov chain | Thiết kế — giai đoạn tới |
| Phân khúc khách hàng | K-Means / hierarchical clustering | Tùy chọn — giai đoạn tới |

---

## 2. Xây dựng Knowledge Base (KB) cho Tư vấn

### 2.1 Tổng quan thiết kế KB

Knowledge Base trong `chatbot-service` là kho tri thức lai (hybrid) kết hợp hai nguồn dữ liệu bổ sung cho nhau:

- **Tài liệu tĩnh:** Chính sách, FAQ — được seed vào cơ sở dữ liệu khi khởi động.
- **Tài liệu sản phẩm động:** Đồng bộ từ ba dịch vụ danh mục sản phẩm (`cloth-service`, `laptop-service`, `mobile-service`).

### 2.2 Mô hình dữ liệu KB

Lược đồ được định nghĩa trong `apps/chatbot/models.py`:

```python
class KnowledgeDocument(models.Model):
    SOURCE_POLICY   = "policy"
    SOURCE_FAQ      = "faq"
    SOURCE_PRODUCT  = "product"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title           = models.CharField(max_length=255)
    source_type     = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    source_id       = models.CharField(max_length=255, blank=True)
    product_service = models.CharField(max_length=32, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)


class KnowledgeChunk(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document    = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE,
                                    related_name="chunks")
    chunk_index = models.PositiveIntegerField(default=0)
    content     = models.TextField()
    embedding   = models.JSONField(null=True, blank=True)  # vector 1536 chiều
    updated_at  = models.DateTimeField(auto_now=True)
```

Mỗi `KnowledgeDocument` được chia thành nhiều `KnowledgeChunk` với kích thước xấp xỉ 400 ký tự, có độ chồng lấp 80 ký tự giữa các chunk liên tiếp để đảm bảo ngữ cảnh không bị cắt đứt.

### 2.3 Tài liệu tĩnh (Static KB)

Hệ thống seed sẵn các tài liệu chính sách và FAQ vào database khi khởi động (`python manage.py seed_kb`). Các tài liệu hiện có:

| Loại | Tiêu đề | Nội dung |
|---|---|---|
| Policy | Return Policy | Hoàn trả trong 30 ngày, xử lý hoàn tiền 5–7 ngày |
| Policy | Shipping Policy | Giao hàng tiêu chuẩn 3–5 ngày, miễn phí đơn trên $50 |
| Policy | Payment Methods | Chấp nhận Visa, Mastercard, PayPal, chuyển khoản |
| Policy | Warranty | Điện tử 12 tháng, quần áo 90 ngày |
| FAQ | How do I track my order? | Kiểm tra qua email hoặc mục Orders trong tài khoản |
| FAQ | Can I cancel my order? | Huỷ trong 1 giờ đầu sau khi đặt |
| FAQ | Can I change my delivery address? | Liên hệ trước khi giao hàng |
| FAQ | What if a product is out of stock? | Kiểm tra lại sau hoặc liên hệ để được thông báo |

### 2.4 Tài liệu sản phẩm động (Dynamic KB)

Module `product_fetcher.py` kéo dữ liệu từ ba dịch vụ catalog thông qua REST API nội bộ và chuẩn hóa thành văn bản mô tả tự nhiên:

```python
PRODUCT_SOURCES = [
    {
        "service": "cloth",
        "base_url_setting": "CLOTH_SERVICE_URL",
        "resource": "cloth-products",
        "extra_fields": ["size", "material", "color", "gender"],
    },
    {
        "service": "laptop",
        "base_url_setting": "LAPTOP_SERVICE_URL",
        "resource": "laptop-products",
        "extra_fields": ["brand", "cpu", "ram_gb", "storage_gb", "display_size"],
    },
    {
        "service": "mobile",
        "base_url_setting": "MOBILE_SERVICE_URL",
        "resource": "mobile-products",
        "extra_fields": ["brand", "operating_system", "screen_size",
                         "battery_mah", "camera_mp"],
    },
]
```

Mỗi sản phẩm được chuyển thành văn bản theo định dạng:

```
Product: Dell XPS 15. Description: Premium thin-and-light laptop...
Price: $1299.99. In stock: 8 units. Active: Yes.
Brand: Dell. Cpu: Intel Core i7-13700H. Ram Gb: 16. Storage Gb: 512. Display Size: 15.6
```

### 2.5 Cơ chế upsert và đồng bộ KB

Hàm `_upsert_document_with_chunks()` trong `kb_service.py` đảm bảo KB luôn được cập nhật mà không tạo bản ghi trùng lặp:

1. `update_or_create` trên `KnowledgeDocument` theo `(source_type, source_id)`.
2. Chia nội dung thành các chunk, `update_or_create` từng `KnowledgeChunk`.
3. Xóa các chunk cũ không còn tồn tại (tài liệu bị rút ngắn).
4. Nếu `USE_EMBEDDING_RETRIEVAL=1`, gọi API embedding OpenAI cho mỗi chunk.

Lệnh đồng bộ thủ công:

```bash
python manage.py sync_kb    # sync sản phẩm từ catalog
python manage.py seed_kb    # seed tài liệu tĩnh
```

Hoặc qua API nội bộ:

```
POST /api/internal/kb/sync
Header: X-Internal-Service-Token: <token>
```

---

## 3. Áp dụng RAG để Xây dựng Chat Tư vấn

### 3.1 Kiến trúc RAG (Retrieval-Augmented Generation)

RAG là kỹ thuật kết hợp hệ thống truy xuất thông tin (Retrieval) với mô hình ngôn ngữ lớn (LLM) để tạo ra câu trả lời có căn cứ thực tế. Thay vì để LLM tự suy luận từ tham số đã học, RAG cung cấp ngữ cảnh từ kho tri thức cụ thể của hệ thống, qua đó:

- Loại bỏ hiện tượng "hallucination" (bịa đặt thông tin).
- Đảm bảo câu trả lời dựa trên dữ liệu sản phẩm và chính sách thực tế.
- Cho phép cập nhật KB mà không cần huấn luyện lại mô hình.

### 3.2 Quy trình RAG đầy đủ

Luồng xử lý được triển khai trong `rag_service.py`:

```
1. Khách hàng gửi POST /api/chat với { question, conversation_id? }
2. chatbot-service xác thực JWT của khách hàng
3. Load hoặc tạo mới ChatConversation
4. Truy xuất top-K chunk liên quan từ KB:
   a. Nếu USE_EMBEDDING_RETRIEVAL=0: Lexical retrieval (mặc định)
   b. Nếu USE_EMBEDDING_RETRIEVAL=1: Embedding cosine similarity
5. Xây dựng context window:
   [System prompt + retrieved chunks] + [lịch sử hội thoại] + [câu hỏi hiện tại]
6. Gọi OpenAI chat completions (gpt-4o-mini)
7. Lưu ChatMessage (user + assistant) vào database
8. Trả về { answer, citations, conversation_id }
```

### 3.3 Chiến lược Truy xuất (Retrieval Strategies)

Hệ thống hỗ trợ hai chiến lược truy xuất, có thể cấu hình qua biến môi trường:

#### Chiến lược A — Lexical Retrieval (mặc định)

Triển khai trong `retriever.py`, không phụ thuộc API bên ngoài:

```python
def lexical_retrieve(question: str, chunks, top_k: int = 5):
    question_tokens = {t for t in _tokenize(question) if t not in _STOPWORDS}
    scored = []
    for chunk in chunk_list:
        chunk_tokens = {t for t in _tokenize(chunk.content) if t not in _STOPWORDS}
        overlap = len(question_tokens & chunk_tokens)
        if overlap > 0:
            scored.append((chunk, overlap))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored[:top_k]]
```

Tokenization sử dụng regex `[a-z0-9]+` và loại bỏ stopword tiếng Anh phổ biến. Phương pháp này xác định, không tốn chi phí API và đủ hiệu quả cho KB tập trung.

#### Chiến lược B — Embedding-based Retrieval (tùy chọn)

Khi `USE_EMBEDDING_RETRIEVAL=1`:

1. **Lúc sync KB:** Mỗi chunk được embed bằng `text-embedding-3-small` (1536 chiều), lưu vào cột `embedding` (JSONField).
2. **Lúc chat:** Câu hỏi được embed real-time, tính cosine similarity với tất cả chunk.

```python
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
```

### 3.4 System Prompt và Xây dựng Context

System prompt được thiết kế để ràng buộc LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp:

```
You are a helpful shopping assistant for an e-commerce store that sells
clothing, laptops, and mobile phones.

Answer the customer's question using ONLY the information in the Context
sections below. If the answer cannot be found in the context, say so
honestly and suggest the customer contact support@store.com.

Be concise, friendly, and helpful. When mentioning products, include
the price if you know it.

Context:
{retrieved_chunks}
```

Cấu trúc prompt hoàn chỉnh được ghép theo thứ tự:

```
[System message với context]
[Lịch sử hội thoại — tối đa 6 tin nhắn gần nhất]
[Câu hỏi hiện tại của người dùng]
```

### 3.5 Quản lý hội thoại đa lượt (Multi-turn Conversation)

Mô hình dữ liệu hội thoại:

```python
class ChatConversation(models.Model):
    id       = models.UUIDField(primary_key=True)
    user_id  = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    conversation = models.ForeignKey(ChatConversation, related_name="messages")
    role         = models.CharField()   # 'user' | 'assistant'
    content      = models.TextField()
    citations    = models.JSONField()   # danh sách chunk được dùng
    created_at   = models.DateTimeField(auto_now_add=True)
```

Khách hàng có thể tiếp tục hội thoại bằng cách gửi `conversation_id` trong request tiếp theo. Hệ thống tải lại 6 tin nhắn gần nhất (cấu hình bởi `CONVERSATION_HISTORY_LIMIT`) để đưa vào prompt, cho phép chatbot hiểu ngữ cảnh các câu hỏi follow-up.

### 3.6 Ví dụ tương tác thực tế

**Request:**

```json
POST /api/chat
Authorization: Bearer <jwt>

{
  "question": "Do you have a laptop with 32GB RAM under $2000?",
  "conversation_id": null
}
```

**Response:**

```json
{
  "answer": "Yes, we currently carry the Dell XPS 15 with 32GB RAM at $1,799. It runs an Intel Core i7 CPU and has 1TB SSD storage. Would you like to add it to your cart?",
  "conversation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_title": "Dell XPS 15 Laptop",
      "snippet": "RAM: 32 GB. Price: $1799. Brand: Dell..."
    }
  ]
}
```

### 3.7 Kiểm thử (Testing)

Bộ test tích hợp trong `tests/test_chat_api.py` bao gồm các tình huống:

| Test case | Mô tả |
|---|---|
| `test_chat_returns_answer` | Chat trả về đúng cấu trúc response (answer, conversation\_id, citations) |
| `test_chat_requires_auth` | Từ chối request không có JWT (HTTP 401/403) |
| `test_chat_rejects_empty_question` | Từ chối câu hỏi rỗng (HTTP 400) |
| `test_chat_continues_conversation` | Hội thoại đa lượt giữ nguyên conversation\_id |

OpenAI được mock hoàn toàn trong test để tránh chi phí API thực tế.

---

## 4. Deploy và Tích hợp trong Hệ E-Commerce

### 4.1 Kiến trúc tổng thể hệ thống

Hệ thống gồm 9 microservice, mỗi service có database riêng biệt:

| Service | Port | Database | Vai trò |
|---|---|---|---|
| `web-service` | 8000 | SQLite | Browser-facing BFF |
| `staff-service` | 8001 | staff\_db | Quản lý nhân viên, sản phẩm |
| `customer-service` | 8002 | customer\_db | Xác thực, giỏ hàng, đơn hàng |
| `cloth-service` | 8003 | cloth\_db | Danh mục quần áo |
| `laptop-service` | 8004 | laptop\_db | Danh mục laptop |
| `mobile-service` | 8005 | mobile\_db | Danh mục điện thoại |
| **`chatbot-service`** | **8006** | **chatbot\_db** | **KB + RAG chatbot (đã triển khai)** |
| `behavior-service` | 8007 | behavior\_db | Tracking sự kiện (giai đoạn tới) |
| `recommendation-service` | 8008 | — | Inference ML (giai đoạn tới) |

### 4.2 Sơ đồ kiến trúc

```
Customer Browser
       │
       ▼
  web-service :8000
  ┌────┬────┬────────────────────────────────┐
  │    │    │                                │
  ▼    ▼    ▼                                ▼
cust  chat  behavior(*)            recommendation(*)
svc   svc   svc                    svc
:8002 :8006 :8007                  :8008
        │
        ├──► cloth-service :8003  ──► cloth_db
        ├──► laptop-service :8004 ──► laptop_db
        ├──► mobile-service :8005 ──► mobile_db
        ├──► OpenAI API (gpt-4o-mini)
        └──► chatbot_db (PostgreSQL)

(*) = giai đoạn tới
```

### 4.3 Cấu hình Docker Compose

`chatbot-service` và `chatbot-db` được thêm vào `docker-compose.yml`:

```yaml
chatbot-service:
  build:
    context: ./services/chatbot-service
  container_name: chatbot-service
  env_file: .env
  environment:
    DJANGO_SETTINGS_MODULE: config.settings.local
    PYTHONUNBUFFERED: "1"
  volumes:
    - ./services/chatbot-service:/app
    - ./shared:/app/shared
  ports:
    - "${CHATBOT_SERVICE_PORT:-8006}:8000"
  depends_on:
    - chatbot-db

chatbot-db:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB:       ${CHATBOT_DB_NAME}
    POSTGRES_USER:     ${CHATBOT_DB_USER}
    POSTGRES_PASSWORD: ${CHATBOT_DB_PASSWORD}
  ports:
    - "5438:5432"
  volumes:
    - chatbot_db_data:/var/lib/postgresql/data
```

### 4.4 Biến môi trường cấu hình

```bash
# Chatbot service
CHATBOT_SERVICE_PORT=8006
CHATBOT_DB_NAME=chatbot_db
CHATBOT_DB_USER=chatbot_user
CHATBOT_DB_PASSWORD=chatbot_password
CHATBOT_DB_HOST=chatbot-db
CHATBOT_DB_PORT=5432

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
USE_EMBEDDING_RETRIEVAL=0   # 0=lexical (default), 1=embedding

# Kết nối dịch vụ catalog
CLOTH_SERVICE_URL=http://cloth-service:8000
LAPTOP_SERVICE_URL=http://laptop-service:8000
MOBILE_SERVICE_URL=http://mobile-service:8000

# Tham số RAG
KB_RETRIEVAL_TOP_K=5
CONVERSATION_HISTORY_LIMIT=6
```

### 4.5 Quy trình khởi động dịch vụ

```bash
# Khởi động service và database
docker compose up --build chatbot-service chatbot-db

# Migrate database schema
docker compose exec chatbot-service python manage.py migrate

# Seed tài liệu tĩnh (chính sách, FAQ)
docker compose exec chatbot-service python manage.py seed_kb

# Đồng bộ sản phẩm từ catalog services
docker compose exec chatbot-service python manage.py sync_kb
```

### 4.6 Thiết kế API

#### `POST /api/chat` — Chatbot tư vấn

- **Xác thực:** JWT của khách hàng (`Bearer <token>`)
- **Xử lý:** `ChatView` → `answer_question()` → RAG pipeline → OpenAI

#### `POST /api/internal/kb/sync` — Đồng bộ Knowledge Base

- **Xác thực:** `X-Internal-Service-Token` (service-to-service)
- **Xử lý:** `KBSyncView` → `run_full_sync()` → seed static + sync products
- **Response:** `{ synced_documents, synced_chunks, duration_ms }`

### 4.7 Tích hợp với web-service

`web-service` tích hợp chatbot qua `ChatbotGateway`, theo đúng pattern đã có của `CustomerGateway` và `StaffGateway`:

```python
class ChatbotGateway(BaseGatewayClient):
    def chat(self, question: str, conversation_id: str | None, jwt: str):
        return self._request(
            "post",
            f"{settings.CHATBOT_SERVICE_URL}/api/chat",
            json={"question": question, "conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {jwt}"},
        )
```

Luồng tích hợp hoàn chỉnh:

1. Khách hàng nhập câu hỏi vào chat widget trên `web-service`.
2. `web-service` gửi AJAX/form POST tới Django view.
3. Django view proxy request (kèm session JWT) sang `chatbot-service`.
4. `chatbot-service` chạy RAG pipeline, trả về câu trả lời có trích dẫn.
5. `web-service` render câu trả lời trong chat widget.
6. Khách hàng có thể hỏi tiếp theo với cùng `conversation_id`.

### 4.8 Bảo mật và xác thực

- **Customer endpoint** (`/api/chat`): Sử dụng `JWTAuthentication` + `IsCustomerUser` để đảm bảo chỉ khách hàng đã đăng nhập mới có thể chat. `user_id` được trích xuất từ JWT và gắn với `ChatConversation`, ngăn khách hàng này truy cập hội thoại của khách hàng khác.
- **Internal endpoint** (`/api/internal/kb/sync`): Sử dụng `InternalServiceAuthentication` với `INTERNAL_SERVICE_TOKEN`, theo đúng pattern xác thực service-to-service của toàn hệ thống.

### 4.9 Stack công nghệ

| Thành phần | Công nghệ |
|---|---|
| Framework | Django 5.1, Django REST Framework 3.15 |
| Database | PostgreSQL 16 (chatbot\_db riêng biệt) |
| LLM | OpenAI gpt-4o-mini |
| Embedding | OpenAI text-embedding-3-small (tùy chọn) |
| Xác thực | PyJWT 2.9 |
| HTTP client | requests 2.32 |
| Containerization | Docker, Docker Compose |

---

## 5. Kết luận

### 5.1 Kết quả đạt được

Trong phạm vi iteration này, nhóm đã hoàn thành triển khai đầy đủ module `chatbot-service` — một microservice độc lập với cơ sở dữ liệu riêng — bao gồm:

- **Knowledge Base lai:** Kết hợp tài liệu tĩnh (chính sách, FAQ) và tài liệu sản phẩm động được đồng bộ từ ba dịch vụ catalog.
- **Chunking thông minh:** Chia văn bản thành các chunk 400 ký tự với độ chồng lấp 80 ký tự để bảo toàn ngữ cảnh.
- **RAG pipeline hoàn chỉnh:** Lexical retrieval mặc định (không chi phí API) và embedding-based retrieval tùy chọn (độ chính xác cao hơn).
- **Multi-turn conversation:** Duy trì lịch sử hội thoại qua `conversation_id`, hỗ trợ câu hỏi follow-up tự nhiên.
- **Bộ kiểm thử:** Test tích hợp với mock OpenAI cho 4 tình huống cốt lõi.
- **Tích hợp hoàn toàn:** API thiết kế nhất quán với kiến trúc microservices hiện có, sử dụng lại cơ chế JWT và internal token authentication.

### 5.2 Hướng phát triển tiếp theo

Giai đoạn tiếp theo sẽ triển khai `behavior-service` để thu thập sự kiện hành vi và `recommendation-service` để cá nhân hóa trang chủ, từ đó hoàn thiện vòng lặp AI: **thu thập hành vi → huấn luyện mô hình → gợi ý cá nhân hóa → tư vấn qua chatbot**.

---

*Tài liệu kỹ thuật chi tiết: `docs/chatbot-architecture.md`*
