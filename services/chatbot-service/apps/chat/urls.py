from django.urls import path

from apps.chat.views import ChatAPIView, ChatContextAPIView

urlpatterns = [
    path("chat", ChatAPIView.as_view()),
    path("chat/context", ChatContextAPIView.as_view()),
]
