from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    domain = serializers.CharField(max_length=32, required=False, allow_blank=True)
    page_context = serializers.CharField(max_length=64, required=False, allow_blank=True)
    product_id = serializers.UUIDField(required=False, allow_null=True)


class CitationSerializer(serializers.Serializer):
    chunk_id = serializers.UUIDField()
    document_title = serializers.CharField()
    snippet = serializers.CharField()
    source_type = serializers.CharField(required=False, allow_blank=True)
    product_service = serializers.CharField(required=False, allow_blank=True)
    source_id = serializers.CharField(required=False, allow_blank=True)


class ChatResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    conversation_id = serializers.UUIDField()
    citations = CitationSerializer(many=True)


class KBSyncResponseSerializer(serializers.Serializer):
    synced_documents = serializers.IntegerField()
    synced_chunks = serializers.IntegerField()
    duration_ms = serializers.FloatField()
