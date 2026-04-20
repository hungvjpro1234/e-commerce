"""
Knowledge Base management: chunk documents, sync products, seed static content.
"""

import re
import time

from django.conf import settings

from apps.chatbot.models import KnowledgeChunk, KnowledgeDocument
from apps.chatbot.product_fetcher import fetch_all_products

MAX_CHUNK_CHARS = 550


def _split_long_paragraph(paragraph: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph.strip())
    chunks = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > MAX_CHUNK_CHARS:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks or [paragraph.strip()]


def _split_into_chunks(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []

    chunks = []
    for paragraph in paragraphs:
        if len(paragraph) <= MAX_CHUNK_CHARS:
            chunks.append(paragraph)
        else:
            chunks.extend(_split_long_paragraph(paragraph))
    return chunks


def _embed_chunk(content: str) -> list[float] | None:
    """
    Return an embedding vector for the chunk if embedding retrieval is enabled.
    Returns None if embeddings are disabled or if the API call fails.
    """
    if not settings.USE_EMBEDDING_RETRIEVAL:
        return None

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return None

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=content,
        )
        return response.data[0].embedding
    except Exception:
        return None


def _upsert_document_with_chunks(
    title: str,
    content: str,
    source_type: str,
    source_id: str = "",
    product_service: str = "",
    category_label: str = "",
) -> tuple[KnowledgeDocument, int]:
    """
    Create or update a KnowledgeDocument and its associated chunks.
    Returns (document, number_of_chunks_written).
    """
    doc, _ = KnowledgeDocument.objects.update_or_create(
        source_type=source_type,
        source_id=source_id if source_id else title,
        defaults={
            "title": title,
            "product_service": product_service,
        },
    )

    texts = _split_into_chunks(content)
    existing_ids = set(
        doc.chunks.values_list("chunk_index", flat=True)
    )

    for idx, chunk_text in enumerate(texts):
        embedding = _embed_chunk(chunk_text)
        chunk, created = KnowledgeChunk.objects.update_or_create(
            document=doc,
            chunk_index=idx,
            defaults={"content": chunk_text, "embedding": embedding},
        )
        existing_ids.discard(idx)

    # Remove stale chunks if document was shortened
    if existing_ids:
        doc.chunks.filter(chunk_index__in=existing_ids).delete()

    return doc, len(texts)


def sync_products() -> tuple[int, int]:
    """
    Fetch products from all catalog services and upsert them into the KB.
    Returns (documents_synced, chunks_synced).
    """
    products = fetch_all_products()
    total_docs = 0
    total_chunks = 0

    for product in products:
        _doc, n_chunks = _upsert_document_with_chunks(
            title=product["title"],
            content=product["content"],
            source_type=KnowledgeDocument.SOURCE_PRODUCT,
            source_id=product["source_id"],
            product_service=product["product_service"],
            category_label=product.get("category_label", ""),
        )
        total_docs += 1
        total_chunks += n_chunks

    return total_docs, total_chunks


STATIC_KB: list[dict] = [
    {
        "source_id": "return-policy",
        "source_type": KnowledgeDocument.SOURCE_POLICY,
        "title": "Return Policy",
        "content": (
            "You can return any item within 30 days of purchase for a full refund. "
            "Items must be unused and in original packaging. "
            "To initiate a return, contact us at support@store.com with your order number. "
            "Refunds are processed within 5-7 business days after we receive the item."
        ),
    },
    {
        "source_id": "shipping-policy",
        "source_type": KnowledgeDocument.SOURCE_POLICY,
        "title": "Shipping Policy",
        "content": (
            "Standard shipping takes 3-5 business days and is free on orders over $50. "
            "Express shipping takes 1-2 business days and costs an additional $9.99. "
            "We ship to all domestic addresses. International shipping is not yet available. "
            "You will receive a tracking number by email once your order ships."
        ),
    },
    {
        "source_id": "payment-methods",
        "source_type": KnowledgeDocument.SOURCE_POLICY,
        "title": "Payment Methods",
        "content": (
            "We accept Visa, Mastercard, American Express, PayPal, and bank transfers. "
            "All payments are processed securely via our payment gateway. "
            "Payment is taken at the time of checkout. "
            "We do not store your card details."
        ),
    },
    {
        "source_id": "warranty",
        "source_type": KnowledgeDocument.SOURCE_POLICY,
        "title": "Warranty",
        "content": (
            "Electronics, gaming gear, and tech accessories carry a 12-month manufacturer warranty "
            "against defects in materials and workmanship unless otherwise stated on the product page. "
            "Clothing, beauty, food, books, sports equipment, and home items carry a 90-day warranty "
            "against manufacturing defects where applicable. "
            "Warranty does not cover accidental damage or normal wear and tear. "
            "To make a warranty claim, contact support@store.com with your order number and "
            "a description of the issue."
        ),
    },
    {
        "source_id": "faq-track-order",
        "source_type": KnowledgeDocument.SOURCE_FAQ,
        "title": "FAQ: How do I track my order?",
        "content": (
            "After your order ships, you will receive an email with a tracking link. "
            "You can also log in to your account and visit the Orders section to see the "
            "current status of your delivery."
        ),
    },
    {
        "source_id": "faq-cancel-order",
        "source_type": KnowledgeDocument.SOURCE_FAQ,
        "title": "FAQ: Can I cancel my order?",
        "content": (
            "Orders can be cancelled within 1 hour of being placed by contacting our support team. "
            "Once the order has been dispatched we are unable to cancel it, but you can return it "
            "after delivery following our Return Policy."
        ),
    },
    {
        "source_id": "faq-change-address",
        "source_type": KnowledgeDocument.SOURCE_FAQ,
        "title": "FAQ: Can I change my delivery address?",
        "content": (
            "If your order has not yet been dispatched, please contact support@store.com "
            "immediately with your order number and the new address. "
            "We cannot change addresses after an order has been shipped."
        ),
    },
    {
        "source_id": "faq-stock",
        "source_type": KnowledgeDocument.SOURCE_FAQ,
        "title": "FAQ: What if a product is out of stock?",
        "content": (
            "If a product you want is out of stock, you can check back later as we restock regularly. "
            "You can also contact us and we will notify you when it becomes available again."
        ),
    },
]


def seed_static_kb() -> tuple[int, int]:
    """
    Insert or update all static policy and FAQ documents.
    Returns (documents_seeded, chunks_seeded).
    """
    total_docs = 0
    total_chunks = 0

    for entry in STATIC_KB:
        _doc, n_chunks = _upsert_document_with_chunks(
            title=entry["title"],
            content=entry["content"],
            source_type=entry["source_type"],
            source_id=entry["source_id"],
            category_label=entry.get("category_label", ""),
        )
        total_docs += 1
        total_chunks += n_chunks

    return total_docs, total_chunks


def run_full_sync() -> dict:
    """
    Run a full KB sync: seed static content and then sync products.
    Returns a summary dict with counts and duration.
    """
    start = time.monotonic()

    static_docs, static_chunks = seed_static_kb()
    product_docs, product_chunks = sync_products()

    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "synced_documents": static_docs + product_docs,
        "synced_chunks": static_chunks + product_chunks,
        "duration_ms": round(elapsed_ms, 1),
    }
