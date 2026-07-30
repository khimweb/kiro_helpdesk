from django.contrib import admin
from .models import (
    Ticket, TicketComment, Attachment, Category, SLA, TicketHistory,
    AIChatSession, AIChatMessage,
)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'title', 'status', 'priority', 'created_by', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['ticket_id', 'title']
    readonly_fields = ['ticket_id', 'created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ['priority', 'response_time_hours', 'resolution_time_hours', 'is_active']


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'is_internal', 'created_at']


admin.site.register(Attachment)
admin.site.register(TicketHistory)


@admin.register(AIChatSession)
class AIChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'updated_at', 'created_at']
    list_filter = ['updated_at']
    search_fields = ['title', 'user__username']


@admin.register(AIChatMessage)
class AIChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
