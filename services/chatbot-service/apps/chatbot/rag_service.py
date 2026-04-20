"""RAG service: retrieves relevant KB chunks and calls OpenAI to generate answers."""

import logging
import re
import time
import uuid

from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

from apps.chatbot.models import ChatConversation, ChatMessage, KnowledgeChunk
from apps.chatbot.retriever import detect_intent, embedding_retrieve, lexical_retrieve

SYSTEM_PROMPT = """You are a shopping assistant for an e-commerce store.

Rules:
- Use only the facts in the provided context.
- Prefer context from the same product category or product page when available.
- Do not merge details from different products unless the context explicitly compares them.
- If the context is insufficient, say you do not have enough information and suggest support@store.com.
- Keep the answer concise, grounded, and practical.

Context:
{context}
"""


def _build_context(chunks) -> str:
    sections = []
    for i, chunk in enumerate(chunks, 1):
        doc = chunk.document
        meta = f"type={doc.source_type}"
        if doc.product_service:
            meta += f", domain={doc.product_service}"
        if doc.source_id:
            meta += f", source_id={doc.source_id}"
        sections.append(f"[{i}] {doc.title} ({meta})\n{chunk.content}")
    return "\n\n".join(sections)


def _build_history_messages(conversation: ChatConversation, limit: int) -> list[dict]:
    messages = (
        conversation.messages
        .order_by("-created_at")[:limit]
    )
    result = []
    for msg in reversed(list(messages)):
        result.append({"role": msg.role, "content": msg.content})
    return result


def _is_gemini_rate_limit(exc: BaseException) -> bool:
    s = str(exc).lower()
    return "429" in s or "resource exhausted" in s or ("quota" in s and "exceed" in s)


def _is_quota_zero(exc: BaseException) -> bool:
    """Trả True khi limit thực sự = 0 (API key chưa bật / hết hạn mức ngày) — retry vô nghĩa."""
    return "limit: 0" in str(exc)


def _gemini_retry_delay_seconds(exc: BaseException) -> float | None:
    m = re.search(r"retry in ([\d.]+)\s*s", str(exc), re.I)
    if m:
        return min(float(m.group(1)) + 0.5, 90.0)
    return None


def _gemini_model_order() -> list[str]:
    primary = settings.GEMINI_CHAT_MODEL.strip()
    seen = {primary}
    order = [primary]
    for m in getattr(settings, "GEMINI_FALLBACK_MODELS", []):
        if m and m not in seen:
            seen.add(m)
            order.append(m)
    return order


def _call_gemini_one_model(messages: list[dict], model_name: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    system_instruction = None
    if messages and messages[0]["role"] == "system":
        system_instruction = messages[0]["content"]

    history = []
    for msg in messages[1:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    user_content = messages[-1]["content"] if messages else ""
    history.append(types.Content(role="user", parts=[types.Part(text=user_content)]))

    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=512,
        system_instruction=system_instruction,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=history,
        config=config,
    )
    return response.text.strip()


def _call_gemini(messages: list[dict]) -> str | None:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None

    last_error: BaseException | None = None
    for model_name in _gemini_model_order():
        for attempt in range(2):
            try:
                return _call_gemini_one_model(messages, model_name)
            except Exception as exc:
                last_error = exc
                logger.error("[Gemini] model=%s attempt=%d error=%s", model_name, attempt, exc)
                if _is_quota_zero(exc):
                    # limit=0 nghĩa là API chưa được bật hoặc hết hạn mức ngày — không retry
                    break
                if _is_gemini_rate_limit(exc) and attempt == 0:
                    delay = _gemini_retry_delay_seconds(exc)
                    time.sleep(delay if delay is not None else 5.0)
                    continue
                break

    # Tất cả model đều fail → trả None để caller dùng rule-based fallback
    return None


def _rule_based_answer(question: str, chunks) -> str:
    """Fallback khi không có AI: format KB chunks thành câu trả lời có cấu trúc."""
    if not chunks:
        return (
            "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong hệ thống. "
            "Vui lòng liên hệ support@store.com để được hỗ trợ thêm."
        )
    lines = ["Dưới đây là thông tin phù hợp nhất tôi tìm được:\n"]
    for chunk in chunks[:3]:
        lines.append(f"• {chunk.document.title}: {chunk.content.strip()}")
    lines.append("\nNếu cần thêm thông tin, vui lòng liên hệ support@store.com.")
    return "\n".join(lines)


def _base_chunk_queryset(*, domain: str = "", product_id: str = "", intent: str = ""):
    qs = KnowledgeChunk.objects.select_related("document").all()
    if product_id:
        qs = qs.filter(
            Q(document__source_id=product_id)
            | Q(document__source_type__in=["policy", "faq"])
        )
    if domain:
        qs = qs.filter(
            Q(document__product_service=domain)
            | Q(document__product_service="")
        )
    if intent == "policy":
        policy_qs = qs.filter(document__source_type__in=["policy", "faq"])
        if policy_qs.exists():
            return policy_qs
    if intent == "faq":
        faq_qs = qs.filter(document__source_type__in=["faq", "policy"])
        if faq_qs.exists():
            return faq_qs
    return qs


def _retrieve_chunks(
    *,
    question: str,
    top_k: int,
    domain: str = "",
    product_id: str = "",
    page_context: str = "",
):
    intent = detect_intent(question, page_context=page_context)
    filtered_chunks = _base_chunk_queryset(
        domain=domain,
        product_id=product_id,
        intent=intent,
    )

    if settings.USE_EMBEDDING_RETRIEVAL:
        question_embedding = _get_question_embedding(question)
        if question_embedding:
            relevant_chunks = embedding_retrieve(
                question_embedding,
                filtered_chunks,
                top_k=top_k,
                domain=domain,
                product_id=product_id,
                intent=intent,
            )
        else:
            relevant_chunks = lexical_retrieve(
                question,
                filtered_chunks,
                top_k=top_k,
                domain=domain,
                product_id=product_id,
                intent=intent,
            )
    else:
        relevant_chunks = lexical_retrieve(
            question,
            filtered_chunks,
            top_k=top_k,
            domain=domain,
            product_id=product_id,
            intent=intent,
        )

    if relevant_chunks:
        return relevant_chunks[:top_k]

    fallback_chunks = KnowledgeChunk.objects.select_related("document").all()
    return lexical_retrieve(
        question,
        fallback_chunks,
        top_k=top_k,
        domain=domain,
        product_id=product_id,
        intent=intent,
    )


def _call_openai(messages: list[dict], chunks=None) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        gemini_result = _call_gemini(messages)
        if gemini_result is not None:
            return gemini_result
        if chunks is not None:
            question = messages[-1]["content"] if messages else ""
            return _rule_based_answer(question, chunks)
        return (
            "Xin lỗi, chatbot chưa được cấu hình AI. "
            "Vui lòng liên hệ support@store.com để được hỗ trợ."
        )

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        gemini_result = _call_gemini(messages)
        if gemini_result is not None:
            return gemini_result
        if chunks is not None:
            question = messages[-1]["content"] if messages else ""
            return _rule_based_answer(question, chunks)
        return (
            f"I'm sorry, I encountered an error while generating a response. "
            f"Please try again or contact support@store.com. (Error: {exc})"
        )


def _get_question_embedding(question: str) -> list[float] | None:
    api_key = settings.OPENAI_API_KEY
    if not api_key or not settings.USE_EMBEDDING_RETRIEVAL:
        return None
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=question,
        )
        return response.data[0].embedding
    except Exception:
        return None


def answer_question(
    user_id: str,
    question: str,
    conversation_id: uuid.UUID | None = None,
    domain: str = "",
    page_context: str = "",
    product_id: str = "",
) -> dict:
    """
    Full RAG pipeline:
      1. Load or create conversation
      2. Retrieve top-K relevant chunks
      3. Build prompt with context + history
      4. Call OpenAI
      5. Persist messages
      6. Return answer + citations + conversation_id

    Returns:
        {
            "answer": str,
            "conversation_id": UUID,
            "citations": [{"chunk_id", "document_title", "snippet"}, ...],
        }
    """
    top_k = settings.KB_RETRIEVAL_TOP_K
    history_limit = settings.CONVERSATION_HISTORY_LIMIT

    if conversation_id:
        conversation = (
            ChatConversation.objects.filter(id=conversation_id, user_id=user_id).first()
        )
        if not conversation:
            conversation = ChatConversation.objects.create(user_id=user_id)
    else:
        conversation = ChatConversation.objects.create(user_id=user_id)

    relevant_chunks = _retrieve_chunks(
        question=question,
        top_k=top_k,
        domain=domain,
        product_id=product_id,
        page_context=page_context,
    )

    context = _build_context(relevant_chunks)
    history_messages = _build_history_messages(conversation, history_limit)

    system_message = {"role": "system", "content": SYSTEM_PROMPT.format(context=context)}
    user_message = {"role": "user", "content": question}
    messages = [system_message] + history_messages + [user_message]

    answer = _call_openai(messages, chunks=relevant_chunks)

    ChatMessage.objects.create(
        conversation=conversation,
        role=ChatMessage.ROLE_USER,
        content=question,
    )

    citations = [
        {
            "chunk_id": str(chunk.id),
            "document_title": chunk.document.title,
            "snippet": chunk.content[:150],
            "source_type": chunk.document.source_type,
            "product_service": chunk.document.product_service,
            "source_id": chunk.document.source_id,
        }
        for chunk in relevant_chunks
    ]

    ChatMessage.objects.create(
        conversation=conversation,
        role=ChatMessage.ROLE_ASSISTANT,
        content=answer,
        citations=citations,
    )

    return {
        "answer": answer,
        "conversation_id": conversation.id,
        "citations": citations,
    }
