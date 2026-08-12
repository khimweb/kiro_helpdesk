from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.conversation_list, name='messaging_home'),
    path('messages/audio-test/', views.audio_test, name='audio_test'),
    path('messages/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('messages/group/create/', views.create_group, name='create_group'),
    path('messages/group/<int:conversation_id>/edit/', views.edit_group, name='edit_group'),
    # API endpoints
    path('messages/api/send/', views.api_send_message, name='api_send_message'),
    path('messages/api/messages/<int:conversation_id>/', views.api_get_messages, name='api_get_messages'),
    path('messages/api/typing/', views.api_typing_indicator, name='api_typing_indicator'),
    path('messages/api/mark-read/<int:conversation_id>/', views.api_mark_read, name='api_mark_read'),
    path('messages/api/conversations/', views.api_conversations, name='api_conversations'),
    path('messages/api/users/', views.api_user_list, name='api_user_list'),
    path('messages/api/edit/', views.api_edit_message, name='api_edit_message'),
    path('messages/api/delete/', views.api_delete_message, name='api_delete_message'),
    # Call signaling
    path('messages/api/call/initiate/', views.api_initiate_call, name='api_initiate_call'),
    path('messages/api/call/respond/', views.api_respond_call, name='api_respond_call'),
    path('messages/api/call/signal/', views.api_call_signal, name='api_call_signal'),
    path('messages/api/call/status/<int:call_id>/', views.api_call_status, name='api_call_status'),
]
