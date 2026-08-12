from django.contrib import admin
from .models import Conversation, Message, CallLog


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'message_type', 'file', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_type', 'name', 'created_by', 'created_at')
    list_filter = ('conversation_type',)
    filter_horizontal = ('participants',)
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read')
    search_fields = ('content', 'sender__username')


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'caller', 'call_type', 'status', 'started_at')
    list_filter = ('call_type', 'status')
