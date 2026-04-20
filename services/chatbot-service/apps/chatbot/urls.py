from django.urls import path

from apps.chatbot.views import ChatView, KBSyncView

urlpatterns = [
    path("chat", ChatView.as_view(), name="chat"),
    path("internal/kb/sync", KBSyncView.as_view(), name="kb-sync"),
]
