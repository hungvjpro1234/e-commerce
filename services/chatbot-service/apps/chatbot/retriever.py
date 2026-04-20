"""Retrieval strategies for chatbot KB chunks."""

import math
import re
import unicodedata


_STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "of", "to", "and", "or", "for",
    "on", "at", "by", "do", "we", "you", "i", "my", "our", "your", "its",
    "be", "as", "are", "was", "with", "that", "this", "have", "has", "had",
    "from", "not", "but", "if", "so", "any", "all", "can", "will", "about",
    "co", "khong", "la", "va", "cua", "cho", "toi", "minh", "ban", "shop",
    "san", "pham", "hay", "duoc", "voi", "ve", "tai", "tren", "duoi", "co",
    "con", "nhung", "cac", "mot", "nhieu", "gi", "nao", "sao", "bao", "gia",
}

_POLICY_HINTS = {
    "return", "refund", "shipping", "delivery", "warranty", "policy", "cancel",
    "track", "order", "doi", "tra", "hoan", "tien", "giao", "hang", "bao", "hanh",
    "huy",
}

_FAQ_HINTS = {"faq", "how", "when", "where", "can", "lam", "the", "nao"}


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _tokenize(text: str) -> list[str]:
    normalized = _normalize_text(text)
    return re.findall(r"[a-z0-9]+", normalized)


def detect_intent(question: str, page_context: str = "") -> str:
    tokens = set(_tokenize(question))
    if page_context == "product_detail" and tokens & {"compare", "similar", "alternative", "related"}:
        return "product"
    if tokens & _POLICY_HINTS:
        return "policy"
    if tokens & _FAQ_HINTS:
        return "faq"
    return "product"


def _metadata_bonus(chunk, *, domain: str = "", product_id: str = "", intent: str = "") -> float:
    doc = chunk.document
    bonus = 0.0
    if domain and doc.product_service == domain:
        bonus += 6.0
    if product_id and doc.source_id == product_id:
        bonus += 8.0
    if intent and doc.source_type == intent:
        bonus += 4.0
    if intent == "product" and doc.source_type == "product":
        bonus += 2.0
    if intent == "policy" and doc.source_type in {"policy", "faq"}:
        bonus += 1.5
    return bonus


def _score_overlap(question_tokens: set[str], chunk_content: str) -> tuple[int, int]:
    chunk_tokens = [t for t in _tokenize(chunk_content) if t not in _STOPWORDS]
    if not chunk_tokens:
        return 0, 0
    chunk_set = set(chunk_tokens)
    overlap = len(question_tokens & chunk_set)
    phrase_hits = sum(1 for token in question_tokens if token and token in chunk_content.lower())
    return overlap, phrase_hits


def lexical_retrieve(
    question: str,
    chunks,
    top_k: int = 5,
    *,
    domain: str = "",
    product_id: str = "",
    intent: str = "",
):
    chunk_list = list(chunks)
    if not chunk_list:
        return []

    question_tokens = {t for t in _tokenize(question) if t not in _STOPWORDS}
    if not question_tokens:
        return chunk_list[:top_k]

    scored = []
    for chunk in chunk_list:
        overlap, phrase_hits = _score_overlap(question_tokens, chunk.content)
        metadata_bonus = _metadata_bonus(
            chunk,
            domain=domain,
            product_id=product_id,
            intent=intent,
        )
        score = (overlap * 3.0) + phrase_hits + metadata_bonus
        if score > 0:
            scored.append((chunk, score))

    scored.sort(
        key=lambda item: (
            item[1],
            1 if item[0].document.source_id == product_id and product_id else 0,
            item[0].document.updated_at,
        ),
        reverse=True,
    )
    return [chunk for chunk, _ in scored[:top_k]]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embedding_retrieve(
    question_embedding: list[float],
    chunks,
    top_k: int = 5,
    *,
    domain: str = "",
    product_id: str = "",
    intent: str = "",
):
    """
    Return the top-k chunks by cosine similarity against their stored embeddings.

    Args:
        question_embedding: the embedding vector for the question
        chunks: QuerySet or list of KnowledgeChunk instances that have embeddings
        top_k: number of chunks to return
    """
    scored = []
    for chunk in chunks:
        if chunk.embedding:
            score = cosine_similarity(question_embedding, chunk.embedding) + (
                _metadata_bonus(
                    chunk,
                    domain=domain,
                    product_id=product_id,
                    intent=intent,
                ) / 10.0
            )
            scored.append((chunk, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored[:top_k]]
