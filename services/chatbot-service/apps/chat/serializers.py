from rest_framework import serializers

from shared.common.product_domains import PRODUCT_SERVICE_CHOICES


class ChatContextSerializer(serializers.Serializer):
    domain = serializers.ChoiceField(choices=PRODUCT_SERVICE_CHOICES, required=False, allow_blank=True, default="")
    product_id = serializers.CharField(required=False, allow_blank=True, default="")
    page_context = serializers.CharField(required=False, allow_blank=True, default="")
    cart_product_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list,
    )


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=(("user", "user"), ("assistant", "assistant")))
    text = serializers.CharField()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    context = ChatContextSerializer(required=False, default=dict)
    history = ChatMessageSerializer(many=True, required=False, default=list)
    debug = serializers.BooleanField(required=False, default=False)


class ChatContextRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True, default="")
    context = ChatContextSerializer(required=False, default=dict)
