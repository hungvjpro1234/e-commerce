import uuid

from django.db import models


class KnowledgeDocument(models.Model):
    SOURCE_POLICY = "policy"
    SOURCE_FAQ = "faq"
    SOURCE_PRODUCT = "product"
    SOURCE_CHOICES = [
        (SOURCE_POLICY, "Policy"),
        (SOURCE_FAQ, "FAQ"),
        (SOURCE_PRODUCT, "Product"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=255, blank=True, default="")
    product_service = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_type", "title"]

    def __str__(self):
        return f"[{self.source_type}] {self.title}"


class KnowledgeChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.PositiveIntegerField(default=0)
    content = models.TextField()
    # Stored as a JSON list of floats when embedding retrieval is enabled
    embedding = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        unique_together = [("document", "chunk_index")]

    def __str__(self):
        return f"{self.document.title} chunk {self.chunk_index}"


class ChatConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation {self.id} (user {self.user_id})"


class ChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        ChatConversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    # List of {chunk_id, document_title, snippet} dicts used in this reply
    citations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
