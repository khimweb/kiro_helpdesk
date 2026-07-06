from rest_framework import serializers
from .models import Ticket, TicketComment


class TicketSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'ticket_id', 'title', 'description', 'category', 'category_name',
            'priority', 'status', 'created_by', 'created_by_username',
            'assigned_to', 'assigned_to_username', 'created_at', 'updated_at',
            'sla_deadline', 'resolved_at', 'closed_at', 'rating',
        ]
        read_only_fields = ['ticket_id', 'created_by', 'created_at', 'updated_at']


class TicketCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'user', 'user_username', 'content', 'is_internal', 'created_at']
        read_only_fields = ['ticket', 'user', 'created_at']
