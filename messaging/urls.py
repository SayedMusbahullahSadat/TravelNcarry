# messaging/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.inbox, name='inbox'),
    path('messages/conversation/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
]