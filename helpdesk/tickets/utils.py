"""
Utility functions and decorators for the helpdesk tickets app.
"""
import uuid
from datetime import timedelta
from functools import wraps

from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


def generate_ticket_id():
    """Generate a unique ticket ID in the format TICKET-XXXXXXXX."""
    unique_part = uuid.uuid4().hex[:8].upper()
    return f'TICKET-{unique_part}'


def calculate_sla_deadline(priority):
    """
    Calculate the SLA deadline based on ticket priority.
    Falls back to defaults if no SLA rule is configured.
    """
    from tickets.models import SLA
    defaults = {'low': 72, 'medium': 48, 'high': 24, 'critical': 8}
    try:
        sla = SLA.objects.get(priority=priority, is_active=True)
        hours = sla.resolution_time_hours
    except SLA.DoesNotExist:
        hours = defaults.get(priority, 48)
    return timezone.now() + timedelta(hours=hours)


def log_ticket_history(ticket, user, action, description):
    """Record an action in the ticket's history log."""
    from tickets.models import TicketHistory
    TicketHistory.objects.create(
        ticket=ticket,
        user=user,
        action=action,
        description=description,
    )


def get_ticket_status_counts(queryset=None):
    """Return a dict with counts for each ticket status."""
    from tickets.models import Ticket
    qs = queryset if queryset is not None else Ticket.objects.all()
    return {
        'total': qs.count(),
        'open': qs.filter(status='open').count(),
        'in_progress': qs.filter(status='in_progress').count(),
        'resolved': qs.filter(status='resolved').count(),
        'closed': qs.filter(status='closed').count(),
    }


def send_ticket_notification(ticket, event):
    """
    Send email notification for ticket events.
    event: 'created' | 'assigned' | 'status_changed' | 'comment_added'
    """
    from django.core.mail import send_mail
    from django.conf import settings

    subject_map = {
        'created': f'[{ticket.ticket_id}] Your ticket has been created',
        'assigned': f'[{ticket.ticket_id}] Ticket assigned to you',
        'status_changed': f'[{ticket.ticket_id}] Ticket status updated: {ticket.get_status_display()}',
        'comment_added': f'[{ticket.ticket_id}] New comment on your ticket',
    }
    subject = subject_map.get(event, f'Update on ticket {ticket.ticket_id}')
    body = (
        f'Ticket: {ticket.ticket_id}\n'
        f'Title: {ticket.title}\n'
        f'Status: {ticket.get_status_display()}\n'
        f'Priority: {ticket.get_priority_display()}\n'
    )
    recipients = [ticket.created_by.email]
    if ticket.assigned_to and event == 'assigned':
        recipients = [ticket.assigned_to.email]

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
    except Exception:
        pass  # Never let email errors break the app


def role_required(*roles):
    """
    Decorator factory that restricts a view to users with specific roles.
    Usage: @role_required('admin') or @role_required('admin', 'agent')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access that page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
