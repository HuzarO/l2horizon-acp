from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ChatBotView.as_view(), name='chatbot'),
    path('sessions/', views.ChatSessionListView.as_view(), name='chatbot_sessions'),
    path('sessions/<int:session_id>/', views.ChatSessionDetailView.as_view(), name='chatbot_session_detail'),
]
