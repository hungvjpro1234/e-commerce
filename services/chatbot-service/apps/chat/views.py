from rest_framework.views import APIView

from apps.chat.serializers import ChatContextRequestSerializer, ChatRequestSerializer
from apps.chat.services import get_chatbot_service
from shared.common.responses import ok


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        result = get_chatbot_service().chat(
            message=payload["message"],
            context=payload.get("context", {}),
            debug=payload.get("debug", False),
        )
        return ok(result, "Chat response generated.")


class ChatContextAPIView(APIView):
    def post(self, request):
        serializer = ChatContextRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        result = get_chatbot_service().context(
            message=payload.get("message", ""),
            context=payload.get("context", {}),
        )
        return ok(result, "Chat context loaded.")
