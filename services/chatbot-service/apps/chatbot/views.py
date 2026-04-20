from rest_framework.views import APIView

from shared.common.auth import InternalServiceAuthentication, JWTAuthentication
from shared.common.permissions import IsCustomerUser
from shared.common.responses import fail, ok

from apps.chatbot.kb_service import run_full_sync
from apps.chatbot.rag_service import answer_question
from apps.chatbot.serializers import ChatRequestSerializer


class ChatView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomerUser]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid request.", errors=serializer.errors)

        question = serializer.validated_data["question"]
        conversation_id = serializer.validated_data.get("conversation_id")
        domain = serializer.validated_data.get("domain") or ""
        page_context = serializer.validated_data.get("page_context") or ""
        product_id = serializer.validated_data.get("product_id")
        user_id = str(request.user.id)

        result = answer_question(
            user_id=user_id,
            question=question,
            conversation_id=conversation_id,
            domain=domain,
            page_context=page_context,
            product_id=str(product_id) if product_id else "",
        )

        return ok(
            {
                "answer": result["answer"],
                "conversation_id": str(result["conversation_id"]),
                "citations": result["citations"],
            }
        )


class KBSyncView(APIView):
    authentication_classes = [InternalServiceAuthentication]

    def post(self, request):
        result = run_full_sync()
        return ok(result)
