from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse

from .models import (
    Ticket, TicketComment, Attachment, Category, SLA, TicketHistory,
    AIChatSession, AIChatMessage,
)
from .forms import (
    TicketCreateForm, TicketUpdateForm, TicketCommentForm,
    TicketRatingForm, CategoryForm, SLAForm, TicketSearchForm,
)
from .utils import (
    generate_ticket_id, calculate_sla_deadline,
    log_ticket_history, get_ticket_status_counts,
    send_ticket_notification, role_required,
)
from .ai_service import call_openai, is_openai_configured


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    user = request.user

    if user.is_admin:
        tickets_qs = Ticket.objects.all()
    elif user.role == 'manager_it':
        from .models import TicketAssignment
        tickets_qs = Ticket.objects.filter(
            Q(assignment__assigned_to_manager=user) | Q(status='open')
        )
    elif user.role == 'it_staff':
        from .models import TicketAssignment
        tickets_qs = Ticket.objects.filter(
            Q(assignment__assigned_to_it_staff=user) | Q(assigned_to=user)
        )
    elif user.is_agent:
        tickets_qs = Ticket.objects.filter(
            Q(assigned_to=user) | Q(status='open')
        )
    else:
        tickets_qs = Ticket.objects.filter(created_by=user)

    stats = get_ticket_status_counts(tickets_qs)
    recent_tickets = tickets_qs.select_related('created_by', 'assigned_to', 'category')[:10]

    sla_breached = tickets_qs.filter(
        sla_deadline__lt=timezone.now(),
        status__in=['open', 'in_progress']
    ).count()

    from accounts.models import User as UserModel
    all_users = UserModel.objects.all().order_by('username') if user.is_admin or user.is_agent else None

    # For regular users — show their tickets with assignment progress
    user_ticket_progress = []
    if user.is_regular_user:
        from .models import TicketAssignment
        my_tickets = Ticket.objects.filter(created_by=user).order_by('-created_at')[:10]
        for t in my_tickets:
            try:
                a = t.assignment
            except Exception:
                a = None
            user_ticket_progress.append({'ticket': t, 'assignment': a})

    context = {
        'stats': stats,
        'recent_tickets': recent_tickets,
        'sla_breached': sla_breached,
        'all_users': all_users,
        'user_ticket_progress': user_ticket_progress,
    }
    return render(request, 'tickets/dashboard.html', context)


# ── Ticket CRUD ───────────────────────────────────────────────────────────────

@login_required
def ticket_list_view(request):
    user = request.user

    if user.is_admin:
        qs = Ticket.objects.all()
    elif user.is_agent:
        qs = Ticket.objects.filter(Q(assigned_to=user) | Q(status='open'))
    else:
        qs = Ticket.objects.filter(created_by=user)

    qs = qs.select_related('created_by', 'assigned_to', 'category')

    form = TicketSearchForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        status = form.cleaned_data.get('status')
        priority = form.cleaned_data.get('priority')
        category = form.cleaned_data.get('category')

        if q:
            qs = qs.filter(
                Q(ticket_id__icontains=q) |
                Q(title__icontains=q) |
                Q(description__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if category:
            qs = qs.filter(category=category)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tickets/ticket_list.html', {
        'page_obj': page_obj,
        'form': form,
    })


@login_required
def ticket_create_view(request):
    if request.method == 'POST':
        form = TicketCreateForm(request.POST)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.ticket_id = generate_ticket_id()
            ticket.created_by = request.user
            ticket.sla_deadline = calculate_sla_deadline(ticket.priority)
            ticket.save()

            for f in files:
                Attachment.objects.create(ticket=ticket, file=f, uploaded_by=request.user)

            log_ticket_history(ticket, request.user, 'Created', 'Ticket created.')
            send_ticket_notification(ticket, 'created')
            
            # Send Telegram notification for ticket creation
            from .notifications import send_change_alert
            send_change_alert(
                user=request.user,
                action='create',
                object_type='ticket',
                object_info=f'Ticket #{ticket.ticket_id}: {ticket.title}',
                details=f'Priority: {ticket.get_priority_display()}, Category: {ticket.category.name if ticket.category else "None"}'
            )
            
            # Add iOS-style notification data to session
            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'Ticket Created',
                'message': f'Ticket #{ticket.ticket_id} created successfully',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }
            
            messages.success(request, f'Ticket {ticket.ticket_id} created successfully.')
            return redirect('ticket_detail', ticket_id=ticket.ticket_id)
    else:
        form = TicketCreateForm()

    return render(request, 'tickets/create_ticket.html', {'form': form})


@login_required
def ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    user = request.user

    # Regular users can only see their own tickets
    if user.is_regular_user and ticket.created_by != user:
        messages.error(request, 'You do not have access to this ticket.')
        return redirect('ticket_list')

    # Comments: ticket owner sees non-internal only; staff see all
    if user.is_regular_user:
        comments = ticket.comments.filter(is_internal=False)
    else:
        comments = ticket.comments.all()

    comment_form = TicketCommentForm(user=user)
    rating_form = TicketRatingForm(instance=ticket)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'comment':
            comment_form = TicketCommentForm(request.POST, request.FILES, user=user)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.user = user
                if user.is_regular_user:
                    comment.is_internal = False
                comment.save()
                # Save attached files
                from .models import CommentAttachment
                for f in request.FILES.getlist('attachments'):
                    CommentAttachment.objects.create(
                        comment=comment,
                        file=f,
                        uploaded_by=user
                    )
                log_ticket_history(ticket, user, 'Comment Added', comment.content[:100])
                send_ticket_notification(ticket, 'comment_added')
                messages.success(request, 'Comment added.')
                return redirect('ticket_detail', ticket_id=ticket_id)

        elif action == 'rate' and ticket.status in ('resolved', 'closed') and user == ticket.created_by:
            rating_form = TicketRatingForm(request.POST, instance=ticket)
            if rating_form.is_valid():
                rating_form.save()
                messages.success(request, 'Thank you for your rating!')
                return redirect('ticket_detail', ticket_id=ticket_id)

    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': ticket.attachments.all(),
        'history': ticket.history.all(),
        'comment_form': comment_form,
        'rating_form': rating_form,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    user = request.user

    if user.is_regular_user:
        messages.error(request, 'Permission denied.')
        return redirect('ticket_detail', ticket_id=ticket_id)

    old_status = ticket.status
    old_assigned = ticket.assigned_to

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket)

        # Handle attachment deletion
        delete_ids = request.POST.getlist('delete_attachment')
        if delete_ids:
            Attachment.objects.filter(id__in=delete_ids, ticket=ticket).delete()

        # Handle new attachment uploads
        new_files = request.FILES.getlist('new_attachments')
        for f in new_files:
            Attachment.objects.create(ticket=ticket, file=f, uploaded_by=user)

        if form.is_valid():
            updated = form.save(commit=False)

            if updated.status == 'resolved' and old_status != 'resolved':
                updated.resolved_at = timezone.now()
            if updated.status == 'closed' and old_status != 'closed':
                updated.closed_at = timezone.now()

            updated.save()

            if old_status != updated.status:
                log_ticket_history(ticket, user, 'Status Changed',
                    f'Status changed from {old_status} to {updated.status}.')
                send_ticket_notification(ticket, 'status_changed')
                try:
                    from .notifications import send_change_alert
                    send_change_alert(user=user, action='update', object_type='ticket',
                        object_info=f'Ticket #{ticket.ticket_id}: {ticket.title}',
                        details=f'Status changed from {old_status} to {updated.status}')
                except Exception:
                    pass

            if old_assigned != updated.assigned_to:
                assignee = updated.assigned_to.username if updated.assigned_to else 'Unassigned'
                log_ticket_history(ticket, user, 'Assigned', f'Ticket assigned to {assignee}.')
                if updated.assigned_to:
                    send_ticket_notification(ticket, 'assigned')
                try:
                    from .notifications import send_change_alert
                    send_change_alert(user=user, action='update', object_type='ticket',
                        object_info=f'Ticket #{ticket.ticket_id}: {ticket.title}',
                        details=f'Assigned to {assignee}')
                except Exception:
                    pass

            request.session['ios_notification'] = {
                'type': 'success', 'title': 'Ticket Updated',
                'message': f'Ticket #{ticket.ticket_id} updated successfully',
                'icon': '✅', 'auto_hide': True, 'duration': 4000
            }
            messages.success(request, 'Ticket updated.')
            return redirect('ticket_detail', ticket_id=ticket_id)
    else:
        form = TicketUpdateForm(instance=ticket)

    return render(request, 'tickets/update_ticket.html', {
        'form': form,
        'ticket': ticket,
        'attachments': ticket.attachments.all(),
    })


@login_required
@role_required('admin')
def ticket_delete_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    if request.method == 'POST':
        # Send Telegram notification before deletion
        from .notifications import send_change_alert
        send_change_alert(
            user=request.user,
            action='delete',
            object_type='ticket',
            object_info=f'Ticket #{ticket.ticket_id}: {ticket.title}',
            details=f'Category: {ticket.category.name if ticket.category else "None"}'
        )
        
        ticket.delete()
        
        # Add iOS-style notification data to session
        request.session['ios_notification'] = {
            'type': 'success',
            'title': 'Ticket Deleted',
            'message': f'Ticket #{ticket_id} deleted successfully',
            'icon': '✅',
            'auto_hide': True,
            'duration': 4000
        }
        
        messages.success(request, f'Ticket {ticket_id} deleted.')
        return redirect('ticket_list')
    return render(request, 'tickets/ticket_confirm_delete.html', {'ticket': ticket})


# ── Category Management (Admin) ───────────────────────────────────────────────

@login_required
@role_required('admin')
def category_list_view(request):
    categories = Category.objects.annotate(ticket_count=Count('tickets')).order_by('name')
    return render(request, 'tickets/category_list.html', {'categories': categories})


@login_required
@role_required('admin')
def category_create_view(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        category = form.save()
        
        # Send Telegram notification for category creation
        from .notifications import send_change_alert
        send_change_alert(
            user=request.user,
            action='create',
            object_type='category',
            object_info=f'Category: {category.name}',
            details=f'Description: {category.description[:100] if category.description else "No description"}'
        )
        
        # Add iOS-style notification data to session
        request.session['ios_notification'] = {
            'type': 'success',
            'title': 'Category Created',
            'message': f'Category "{category.name}" created successfully',
            'icon': '✅',
            'auto_hide': True,
            'duration': 4000
        }
        
        messages.success(request, 'Category created.')
        return redirect('category_list')
    return render(request, 'tickets/category_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required('admin')
def category_update_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    old_name = category.name
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        category = form.save()
        
        # Send Telegram notification for category update
        from .notifications import send_change_alert
        send_change_alert(
            user=request.user,
            action='update',
            object_type='category',
            object_info=f'Category: {category.name}',
            details=f'Updated from "{old_name}" to "{category.name}"'
        )
        
        # Add iOS-style notification data to session
        request.session['ios_notification'] = {
            'type': 'success',
            'title': 'Category Updated',
            'message': f'Category "{category.name}" updated successfully',
            'icon': '✅',
            'auto_hide': True,
            'duration': 4000
        }
        
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'tickets/category_form.html', {'form': form, 'action': 'Update'})


@login_required
@role_required('admin')
def category_delete_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if request.method == 'POST':
        # Send Telegram notification for category deletion
        from .notifications import send_change_alert
        send_change_alert(
            user=request.user,
            action='delete',
            object_type='category',
            object_info=f'Category: {category.name}',
            details=f'Ticket count: {category.tickets.count()}'
        )
        
        category.delete()
        
        # Add iOS-style notification data to session
        request.session['ios_notification'] = {
            'type': 'success',
            'title': 'Category Deleted',
            'message': f'Category "{category.name}" deleted successfully',
            'icon': '✅',
            'auto_hide': True,
            'duration': 4000
        }
        
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'tickets/category_confirm_delete.html', {'category': category})


# ── Reports (Admin) ───────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'agent')
def reports_view(request):
    from accounts.models import User
    import datetime

    # ── Filters from GET params ──────────────────────────────
    date_from_str = request.GET.get('date_from', '')
    date_to_str   = request.GET.get('date_to', '')
    search_user   = request.GET.get('search_user', '').strip()
    filter_status = request.GET.get('status', '')
    filter_priority = request.GET.get('priority', '')
    time_of_day = request.GET.get('time_of_day', '')  # New: morning/afternoon/evening

    qs = Ticket.objects.select_related('created_by', 'assigned_to', 'category')

    date_from = date_to = None
    if date_from_str:
        try:
            date_from = datetime.datetime.strptime(date_from_str, '%Y-%m-%d')
            qs = qs.filter(created_at__gte=date_from)
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.datetime.strptime(date_to_str, '%Y-%m-%d')
            qs = qs.filter(created_at__lte=date_to.replace(hour=23, minute=59, second=59))
        except ValueError:
            pass
    
    # ── Time of Day Filter ───────────────────────────────────
    if time_of_day == 'morning':
        # Morning: 6:00 AM - 11:59 AM
        qs = qs.filter(created_at__hour__gte=6, created_at__hour__lt=12)
    elif time_of_day == 'afternoon':
        # Afternoon: 12:00 PM - 5:59 PM
        qs = qs.filter(created_at__hour__gte=12, created_at__hour__lt=18)
    elif time_of_day == 'evening':
        # Evening: 6:00 PM - 5:59 AM
        qs = qs.filter(Q(created_at__hour__gte=18) | Q(created_at__hour__lt=6))
    
    if search_user:
        qs = qs.filter(
            Q(created_by__username__icontains=search_user) |
            Q(created_by__first_name__icontains=search_user) |
            Q(created_by__last_name__icontains=search_user) |
            Q(assigned_to__username__icontains=search_user)
        )
    if filter_status:
        qs = qs.filter(status=filter_status)
    if filter_priority:
        qs = qs.filter(priority=filter_priority)

    total = qs.count()
    by_status   = {s: qs.filter(status=s).count() for s, _ in Ticket.STATUS_CHOICES}
    by_priority = {p: qs.filter(priority=p).count() for p, _ in Ticket.PRIORITY_CHOICES}
    by_category = (
        Category.objects.annotate(count=Count('tickets')).values('name', 'count').order_by('-count')
    )

    agents = User.objects.filter(role__in=['agent', 'admin'])
    agent_stats = []
    for agent in agents:
        assigned = qs.filter(assigned_to=agent)
        agent_stats.append({
            'agent': agent,
            'total': assigned.count(),
            'resolved': assigned.filter(status='resolved').count(),
            'open': assigned.filter(status='open').count(),
            'in_progress': assigned.filter(status='in_progress').count(),
            'closed': assigned.filter(status='closed').count(),
        })

    # Detailed ticket table (for print / export)
    ticket_rows = qs.order_by('-created_at')

    # ── Excel export ──────────────────────────────────────────
    if request.GET.get('export') == 'excel':
        import io, csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        fname = f"KML_HelpDesk_Report_{datetime.date.today()}.csv"
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        writer = csv.writer(response)
        # Company header rows
        writer.writerow(['KML Software'])
        writer.writerow(['Help Desk Report'])
        writer.writerow(['Location: Phnom Penh, Cambodia'])
        writer.writerow(['Tel: +855 12 345 678  |  Email: support@kmlsoftware.com'])
        writer.writerow([f'Report Generated: {datetime.datetime.now().strftime("%d %B %Y %H:%M")}'])
        if date_from_str or date_to_str:
            writer.writerow([f'Date Range: {date_from_str or "All"} to {date_to_str or "All"}'])
        if time_of_day:
            writer.writerow([f'Time of Day: {time_of_day.title()}'])
        writer.writerow([])
        # Column headers
        writer.writerow([
            'Ticket ID', 'Title', 'Category', 'Priority', 'Status',
            'Created By', 'Assigned To', 'Created Date', 'Resolved Date', 'Rating'
        ])
        for t in ticket_rows:
            writer.writerow([
                t.ticket_id,
                t.title,
                t.category.name if t.category else '—',
                t.get_priority_display(),
                t.get_status_display(),
                t.created_by.get_full_name() or t.created_by.username,
                t.assigned_to.get_full_name() if t.assigned_to else '—',
                t.created_at.strftime('%d/%m/%Y %H:%M'),
                t.resolved_at.strftime('%d/%m/%Y %H:%M') if t.resolved_at else '—',
                t.rating or '—',
            ])
        # Summary footer
        writer.writerow([])
        writer.writerow(['── SUMMARY ──'])
        writer.writerow(['Total Tickets', total])
        for s, c in by_status.items():
            writer.writerow([s.replace('_', ' ').title(), c])
        writer.writerow([])
        writer.writerow(['© KML Software — Phnom Penh, Cambodia'])
        return response

    context = {
        'total': total,
        'by_status': by_status,
        'by_priority': by_priority,
        'by_category': by_category,
        'agent_stats': agent_stats,
        'ticket_rows': ticket_rows,
        # filter state
        'date_from': date_from_str,
        'date_to': date_to_str,
        'search_user': search_user,
        'filter_status': filter_status,
        'filter_priority': filter_priority,
        'time_of_day': time_of_day,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'now': timezone.now(),
    }
    return render(request, 'tickets/reports.html', context)


@login_required
@role_required('admin', 'agent')
def reports_detail_view(request, report_type):
    context = {'report_type': report_type}

    if report_type == 'status':
        data = {s: Ticket.objects.filter(status=s).count() for s, _ in Ticket.STATUS_CHOICES}
        context['data'] = data
        context['title'] = 'Tickets by Status'

    elif report_type == 'priority':
        data = {p: Ticket.objects.filter(priority=p).count() for p, _ in Ticket.PRIORITY_CHOICES}
        context['data'] = data
        context['title'] = 'Tickets by Priority'

    elif report_type == 'category':
        data = Category.objects.annotate(count=Count('tickets')).values('name', 'count')
        context['data'] = data
        context['title'] = 'Tickets by Category'

    elif report_type == 'sla':
        breached = Ticket.objects.filter(
            sla_deadline__lt=timezone.now(), status__in=['open', 'in_progress']
        )
        context['breached_tickets'] = breached
        context['title'] = 'SLA Breached Tickets'

    return render(request, 'tickets/reports_details.html', context)


# ── SLA Management (Admin) ────────────────────────────────────────────────────

@login_required
@role_required('admin')
def sla_list_view(request):
    slas = SLA.objects.all().order_by('priority')
    return render(request, 'tickets/sla_list.html', {'slas': slas})


@login_required
@role_required('admin')
def sla_form_view(request, pk=None):
    instance = get_object_or_404(SLA, pk=pk) if pk else None
    form = SLAForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, 'SLA rule saved.')
        return redirect('sla_list')
    return render(request, 'tickets/sla_form.html', {'form': form, 'instance': instance})


# ── REST API ──────────────────────────────────────────────────────────────────

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status
from .serializers import TicketSerializer, TicketCommentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_ticket_list(request):
    user = request.user
    if request.method == 'GET':
        if user.is_admin:
            qs = Ticket.objects.all()
        elif user.is_agent:
            qs = Ticket.objects.filter(Q(assigned_to=user) | Q(status='open'))
        else:
            qs = Ticket.objects.filter(created_by=user)
        serializer = TicketSerializer(qs, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save(
                created_by=user,
                ticket_id=generate_ticket_id(),
                sla_deadline=calculate_sla_deadline(request.data.get('priority', 'medium')),
            )
            log_ticket_history(ticket, user, 'Created', 'Ticket created via API.')
            return Response(TicketSerializer(ticket).data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    user = request.user

    if request.method == 'GET':
        return Response(TicketSerializer(ticket).data)

    if request.method == 'PUT':
        if user.is_regular_user:
            return Response({'error': 'Permission denied'}, status=drf_status.HTTP_403_FORBIDDEN)
        serializer = TicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if not user.is_admin:
            return Response({'error': 'Permission denied'}, status=drf_status.HTTP_403_FORBIDDEN)
        ticket.delete()
        return Response(status=drf_status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_ticket_comments(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    user = request.user

    if request.method == 'GET':
        if user.is_regular_user:
            comments = ticket.comments.filter(is_internal=False)
        else:
            comments = ticket.comments.all()
        return Response(TicketCommentSerializer(comments, many=True).data)

    if request.method == 'POST':
        serializer = TicketCommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(ticket=ticket, user=user)
            if user.is_regular_user:
                comment.is_internal = False
                comment.save()
            return Response(TicketCommentSerializer(comment).data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)
# ── AI Chat ──────────────────────────────────────────────────────────────────

def _session_to_dict(session):
    return {
        'id': session.id,
        'title': session.title or 'New Chat',
        'updated_at': session.updated_at.isoformat(),
        'created_at': session.created_at.isoformat(),
    }


def _message_to_dict(message):
    return {
        'id': message.id,
        'role': message.role,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
    }


@login_required
def ai_chat_view(request):
    """AI Q&A page with chat history and multi-language OpenAI support."""
    sessions = AIChatSession.objects.filter(user=request.user)[:50]
    session_id = request.GET.get('session')
    active_session = None
    messages_qs = []

    if session_id:
        active_session = AIChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if active_session:
            messages_qs = active_session.messages.exclude(role='system')

    context = {
        'sessions': sessions,
        'active_session': active_session,
        'chat_messages': messages_qs,
        'openai_configured': is_openai_configured(),
    }
    return render(request, 'tickets/ai_chat.html', context)


@login_required
def ai_chat_send_view(request):
    """AJAX: send a user message and get an AI reply (multi-turn, multi-language)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    import json
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body.decode('utf-8') or '{}')
        else:
            data = request.POST
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    user_message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or data.get('session')

    if not user_message:
        return JsonResponse({'error': 'Please enter a message.'}, status=400)
    if len(user_message) > 8000:
        return JsonResponse({'error': 'Message is too long (max 8000 characters).'}, status=400)

    session = None
    if session_id:
        session = AIChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return JsonResponse({'error': 'Chat session not found.'}, status=404)

    if not session:
        session = AIChatSession.objects.create(user=request.user, title='New Chat')

    is_first = not session.messages.filter(role='user').exists()
    user_msg = AIChatMessage.objects.create(
        session=session, role='user', content=user_message
    )
    if is_first:
        session.auto_title_from_message(user_message)

    history = list(
        session.messages.exclude(pk=user_msg.pk)
        .exclude(role='system')
        .order_by('created_at')
        .values('role', 'content')
    )
    # Cap context to last 20 turns for cost/latency
    history = history[-40:]

    assistant_text, error = call_openai(history, user_message)
    if error:
        # Keep user message; surface error as assistant-side failure without fake answer
        session.save(update_fields=['updated_at'])
        return JsonResponse({
            'error': error,
            'session': _session_to_dict(session),
            'user_message': _message_to_dict(user_msg),
            'openai_configured': is_openai_configured(),
        }, status=502)

    assistant_msg = AIChatMessage.objects.create(
        session=session, role='assistant', content=assistant_text
    )
    session.save(update_fields=['updated_at'])

    return JsonResponse({
        'session': _session_to_dict(session),
        'user_message': _message_to_dict(user_msg),
        'assistant_message': _message_to_dict(assistant_msg),
        'openai_configured': is_openai_configured(),
    })


@login_required
def ai_chat_sessions_view(request):
    """AJAX: list chat history for the current user."""
    sessions = AIChatSession.objects.filter(user=request.user)[:50]
    return JsonResponse({
        'sessions': [_session_to_dict(s) for s in sessions],
    })


@login_required
def ai_chat_session_detail_view(request, session_id):
    """AJAX: load messages for one chat session."""
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user)
    messages_qs = session.messages.exclude(role='system')
    return JsonResponse({
        'session': _session_to_dict(session),
        'messages': [_message_to_dict(m) for m in messages_qs],
    })


@login_required
def ai_chat_new_view(request):
    """AJAX or redirect: start a blank chat (session is created on first message)."""
    if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'session': None, 'messages': []})
    return redirect('ai_chat')


@login_required
def ai_chat_delete_session_view(request, session_id):
    """AJAX: delete a chat from history."""
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({'ok': True, 'deleted_id': session_id})
# ── Notification Test ────────────────────────────────────────────────────────

@login_required
def notification_test_view(request):
    """Test page for iOS-style notifications"""
    return render(request, 'tickets/notification_test.html')


# ── Assign Workflow ───────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'manager_it')
def assign_list_view(request):
    """Assign page: list all tickets with check + send actions."""
    from accounts.models import User as UserModel
    from .models import TicketAssignment

    user = request.user

    if user.is_admin:
        tickets = Ticket.objects.all().select_related('created_by', 'assigned_to', 'category')
    else:
        # Manager IT sees only tickets assigned to them
        tickets = Ticket.objects.filter(
            assignment__assigned_to_manager=user
        ).select_related('created_by', 'assigned_to', 'category')

    # Ensure every ticket has an assignment record
    for t in tickets:
        TicketAssignment.objects.get_or_create(ticket=t)

    # Users grouped by role for send popup
    all_users     = UserModel.objects.filter(role='user').order_by('username')
    managers      = UserModel.objects.filter(role='manager_it').order_by('username')
    it_staff_list = UserModel.objects.filter(role='it_staff').order_by('username')

    context = {
        'tickets': tickets,
        'all_users': all_users,
        'managers': managers,
        'it_staff_list': it_staff_list,
    }
    return render(request, 'tickets/assign_list.html', context)


@login_required
@role_required('admin', 'manager_it', 'it_staff')
def assign_check_view(request, ticket_id):
    """Mark ticket as checked by current role."""
    from .models import TicketAssignment
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    assignment, _ = TicketAssignment.objects.get_or_create(ticket=ticket)
    user = request.user
    now = timezone.now()

    if user.is_admin and not assignment.admin_checked:
        assignment.admin_checked = True
        assignment.admin_checked_by = user
        assignment.admin_checked_at = now
        assignment.save()
        log_ticket_history(ticket, user, 'Admin Checked', f'Ticket checked by Admin {user.username}')
        messages.success(request, f'Ticket {ticket_id} marked as checked.')

    elif user.is_manager_it and not assignment.manager_checked:
        assignment.manager_checked = True
        assignment.manager_checked_by = user
        assignment.manager_checked_at = now
        assignment.save()
        log_ticket_history(ticket, user, 'Manager Checked', f'Ticket checked by Manager {user.username}')
        messages.success(request, f'Ticket {ticket_id} checked by Manager IT.')

    elif user.is_it_staff and not assignment.it_staff_completed:
        assignment.it_staff_completed = True
        assignment.it_staff_completed_by = user
        assignment.it_staff_completed_at = now
        assignment.save()
        # Mark ticket resolved
        ticket.status = 'resolved'
        ticket.resolved_at = now
        ticket.save()
        log_ticket_history(ticket, user, 'Completed', f'Ticket completed by IT Staff {user.username}')
        messages.success(request, f'Ticket {ticket_id} marked as completed.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'stage': assignment.current_stage})

    return redirect('assign_list')


@login_required
@role_required('admin', 'manager_it')
def assign_send_view(request, ticket_id):
    """Send ticket to a specific user."""
    from .models import TicketAssignment
    from accounts.models import User as UserModel

    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    assignment, _ = TicketAssignment.objects.get_or_create(ticket=ticket)
    user = request.user

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        recipient = get_object_or_404(UserModel, pk=recipient_id)
        now = timezone.now()

        if user.is_admin:
            if recipient.role == 'manager_it':
                assignment.assigned_to_manager = recipient
                assignment.assigned_to_manager_at = now
                assignment.save()
                ticket.assigned_to = recipient
                ticket.status = 'in_progress'
                ticket.save()
                log_ticket_history(ticket, user, 'Assigned to Manager',
                    f'Assigned to Manager IT: {recipient.username}')
                messages.success(request, f'Ticket sent to Manager IT: {recipient.username}')
            elif recipient.role == 'it_staff':
                assignment.assigned_to_it_staff = recipient
                assignment.assigned_to_it_staff_at = now
                assignment.save()
                ticket.assigned_to = recipient
                ticket.status = 'in_progress'
                ticket.save()
                log_ticket_history(ticket, user, 'Assigned to IT Staff',
                    f'Assigned to IT Staff: {recipient.username}')
                messages.success(request, f'Ticket sent to IT Staff: {recipient.username}')
            else:
                # Sending back to user (notify)
                log_ticket_history(ticket, user, 'Notified User',
                    f'Notification sent to: {recipient.username}')
                messages.success(request, f'Notification sent to: {recipient.username}')

        elif user.is_manager_it:
            # Manager can only send to IT Staff
            if recipient.role == 'it_staff':
                assignment.assigned_to_it_staff = recipient
                assignment.assigned_to_it_staff_at = now
                assignment.save()
                ticket.assigned_to = recipient
                ticket.status = 'in_progress'
                ticket.save()
                log_ticket_history(ticket, user, 'Assigned to IT Staff',
                    f'Manager assigned to IT Staff: {recipient.username}')
                messages.success(request, f'Ticket sent to IT Staff: {recipient.username}')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    return redirect('assign_list')


@login_required
def ticket_assignment_status(request, ticket_id):
    """JSON endpoint — returns assignment stages for user dashboard."""
    from .models import TicketAssignment
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    # Only ticket owner, admin, manager, it_staff can view
    user = request.user
    if user.is_regular_user and ticket.created_by != user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        a = ticket.assignment
    except TicketAssignment.DoesNotExist:
        return JsonResponse({'stage': 'pending', 'steps': []})

    steps = [
        {'label': 'Submitted', 'done': True, 'icon': 'fa-paper-plane', 'color': '#6C5CE7'},
        {'label': 'Admin Checked', 'done': a.admin_checked,
         'icon': 'fa-user-shield', 'color': '#0984e3',
         'by': a.admin_checked_by.username if a.admin_checked_by else None},
        {'label': 'Sent to Manager', 'done': bool(a.assigned_to_manager),
         'icon': 'fa-user-tie', 'color': '#6c5ce7',
         'by': a.assigned_to_manager.username if a.assigned_to_manager else None},
        {'label': 'Manager Checked', 'done': a.manager_checked,
         'icon': 'fa-clipboard-check', 'color': '#e67e22',
         'by': a.manager_checked_by.username if a.manager_checked_by else None},
        {'label': 'Assigned to IT Staff', 'done': bool(a.assigned_to_it_staff),
         'icon': 'fa-tools', 'color': '#00b894',
         'by': a.assigned_to_it_staff.username if a.assigned_to_it_staff else None},
        {'label': 'Completed', 'done': a.it_staff_completed,
         'icon': 'fa-check-circle', 'color': '#00b894',
         'by': a.it_staff_completed_by.username if a.it_staff_completed_by else None},
    ]
    return JsonResponse({'stage': a.current_stage, 'steps': steps})


# ── Analytics API ─────────────────────────────────────────────────────────────

@login_required
def api_analytics(request):
    """Return ticket analytics data for charts. Admin/agent only."""
    from django.db.models.functions import TruncMonth, TruncDay, TruncYear, ExtractMonth
    from collections import defaultdict
    import calendar

    user = request.user
    period = request.GET.get('period', 'monthly')  # monthly, daily, yearly
    year = request.GET.get('year', str(timezone.now().year))
    month = request.GET.get('month', '')

    # Base queryset
    if user.is_admin or user.is_agent:
        tickets_qs = Ticket.objects.all()
    else:
        tickets_qs = Ticket.objects.filter(created_by=user)

    # Filter by year
    try:
        year_int = int(year)
        tickets_qs = tickets_qs.filter(created_at__year=year_int)
    except (ValueError, TypeError):
        year_int = timezone.now().year
        tickets_qs = tickets_qs.filter(created_at__year=year_int)

    # Monthly data (default)
    if period == 'monthly':
        monthly_data = (
            tickets_qs
            .annotate(month=ExtractMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        # Fill all 12 months
        months_map = {item['month']: item['count'] for item in monthly_data}
        labels = [calendar.month_abbr[i] for i in range(1, 13)]
        data = [months_map.get(i, 0) for i in range(1, 13)]

    elif period == 'daily':
        # Daily for a specific month
        try:
            month_int = int(month) if month else timezone.now().month
        except (ValueError, TypeError):
            month_int = timezone.now().month

        daily_data = (
            tickets_qs
            .filter(created_at__month=month_int)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        days_map = {item['day'].day: item['count'] for item in daily_data}
        import calendar as cal
        num_days = cal.monthrange(year_int, month_int)[1]
        labels = [str(d) for d in range(1, num_days + 1)]
        data = [days_map.get(d, 0) for d in range(1, num_days + 1)]

    elif period == 'yearly':
        yearly_data = (
            Ticket.objects.all()
            .annotate(yr=TruncYear('created_at'))
            .values('yr')
            .annotate(count=Count('id'))
            .order_by('yr')
        )
        labels = [str(item['yr'].year) for item in yearly_data]
        data = [item['count'] for item in yearly_data]

    else:
        labels = []
        data = []

    # Status breakdown (donut chart)
    status_data = (
        tickets_qs
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    status_labels = [item['status'].replace('_', ' ').title() for item in status_data]
    status_counts = [item['count'] for item in status_data]

    # Priority breakdown
    priority_data = (
        tickets_qs
        .values('priority')
        .annotate(count=Count('id'))
        .order_by('priority')
    )
    priority_labels = [item['priority'].title() for item in priority_data]
    priority_counts = [item['count'] for item in priority_data]

    # Calendar events (tickets with dates)
    calendar_events = []
    for t in tickets_qs.only('ticket_id', 'title', 'status', 'created_at', 'sla_deadline')[:200]:
        calendar_events.append({
            'title': t.title[:40],
            'ticket_id': t.ticket_id,
            'date': t.created_at.strftime('%Y-%m-%d'),
            'status': t.status,
        })
        if t.sla_deadline:
            calendar_events.append({
                'title': f'SLA: {t.title[:30]}',
                'ticket_id': t.ticket_id,
                'date': t.sla_deadline.strftime('%Y-%m-%d'),
                'status': 'sla',
            })

    return JsonResponse({
        'labels': labels,
        'data': data,
        'total': sum(data),
        'period': period,
        'year': year_int,
        'status': {'labels': status_labels, 'data': status_counts},
        'priority': {'labels': priority_labels, 'data': priority_counts},
        'calendar_events': calendar_events,
    })
