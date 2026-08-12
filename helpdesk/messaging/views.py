import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, Count
from django.utils import timezone
from django.conf import settings as django_settings

from accounts.models import User
from .models import Conversation, Message, CallLog


@login_required
def audio_test(request):
    """Test page for audio playback debugging."""
    return render(request, 'messaging/audio_test.html')


@login_required
def conversation_list(request):
    """Main messaging page - shows conversation list."""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_msg_time', '-updated_at')

    users = User.objects.exclude(id=request.user.id).filter(is_active=True)

    context = {
        'conversations': conversations,
        'users': users,
        'active_conversation': None,
    }
    return render(request, 'messaging/messaging_home.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation."""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )

    # Mark messages as read
    Message.objects.filter(
        conversation=conversation, is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_msg_time', '-updated_at')

    messages_qs = conversation.messages.select_related('sender', 'call_log').order_by('created_at')
    users = User.objects.exclude(id=request.user.id).filter(is_active=True)

    context = {
        'conversations': conversations,
        'active_conversation': conversation,
        'messages': messages_qs,
        'users': users,
    }
    return render(request, 'messaging/messaging_home.html', context)


@login_required
def start_conversation(request, user_id):
    """Start or open a private conversation with a user."""
    other_user = get_object_or_404(User, id=user_id)

    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        conversation_type='private',
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            conversation_type='private',
            created_by=request.user
        )
        conversation.participants.add(request.user, other_user)

    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def create_group(request):
    """Create a group chat."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        member_ids = request.POST.getlist('members')

        if name and member_ids:
            conversation = Conversation.objects.create(
                name=name,
                conversation_type='group',
                created_by=request.user
            )
            if request.FILES.get('group_icon'):
                conversation.group_icon = request.FILES['group_icon']
                conversation.save()

            conversation.participants.add(request.user)
            for uid in member_ids:
                try:
                    user = User.objects.get(id=uid)
                    conversation.participants.add(user)
                except User.DoesNotExist:
                    pass

            return redirect('conversation_detail', conversation_id=conversation.id)

    users = User.objects.exclude(id=request.user.id).filter(is_active=True)
    return render(request, 'messaging/create_group.html', {'users': users})


@login_required
def edit_group(request, conversation_id):
    """Edit group chat settings."""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, conversation_type='group', participants=request.user
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        member_ids = request.POST.getlist('members')

        if name:
            conversation.name = name
            if request.FILES.get('group_icon'):
                conversation.group_icon = request.FILES['group_icon']
            conversation.save()

            # Update members
            conversation.participants.clear()
            conversation.participants.add(request.user)
            for uid in member_ids:
                try:
                    user = User.objects.get(id=uid)
                    conversation.participants.add(user)
                except User.DoesNotExist:
                    pass

        return redirect('conversation_detail', conversation_id=conversation.id)

    users = User.objects.exclude(id=request.user.id).filter(is_active=True)
    current_members = conversation.participants.exclude(id=request.user.id).values_list('id', flat=True)
    return render(request, 'messaging/edit_group.html', {
        'conversation': conversation,
        'users': users,
        'current_members': list(current_members),
    })


# ─── API Endpoints ────────────────────────────────────────────────────

@login_required
@require_POST
def api_send_message(request):
    """Send a message (text, file, image, voice)."""
    conversation_id = request.POST.get('conversation_id')
    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')
    file = request.FILES.get('file')

    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )

    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        message_type=message_type,
    )

    if file:
        msg.file = file
        if not message_type or message_type == 'text':
            # Auto-detect type
            name = file.name.lower()
            if name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                msg.message_type = 'image'
            elif name.endswith(('.ogg', '.webm', '.mp3', '.wav', '.m4a')):
                msg.message_type = 'voice'
            else:
                msg.message_type = 'file'
        msg.save()

    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])

    return JsonResponse({
        'status': 'ok',
        'message': {
            'id': msg.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'profile_picture': msg.sender.profile_picture.url if msg.sender.profile_picture else None,
            'created_at': msg.created_at.strftime('%I:%M %p'),
            'created_at_full': msg.created_at.isoformat(),
        }
    })


@login_required
def api_get_messages(request, conversation_id):
    """Get messages for a conversation (polling endpoint)."""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )

    after = request.GET.get('after')  # ISO timestamp or message ID
    messages_qs = conversation.messages.select_related('sender', 'call_log')

    if after:
        try:
            after_id = int(after)
            messages_qs = messages_qs.filter(id__gt=after_id)
        except (ValueError, TypeError):
            pass

    # Mark as read
    messages_qs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages_data = []
    for msg in messages_qs.order_by('created_at')[:100]:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'profile_picture': msg.sender.profile_picture.url if msg.sender.profile_picture else None,
            'is_read': msg.is_read,
            'is_edited': msg.is_edited,
            'is_deleted': msg.is_deleted,
            'call_log': {
                'call_type': msg.call_log.call_type,
                'status': msg.call_log.status,
                'duration': str(msg.call_log.ended_at - msg.call_log.started_at).split('.')[0] if msg.call_log.ended_at else None,
            } if msg.call_log else None,
            'created_at': msg.created_at.strftime('%I:%M %p'),
            'created_at_full': msg.created_at.isoformat(),
        })

    return JsonResponse({'messages': messages_data})


@login_required
@require_POST
def api_typing_indicator(request):
    """Store typing status (simple approach using cache-like pattern)."""
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    is_typing = data.get('is_typing', False)

    # We'll use a simple in-memory approach via session or return to other users via polling
    # Store in a global dict (simple approach for dev)
    from django.core.cache import cache
    key = f"typing_{conversation_id}_{request.user.id}"
    if is_typing:
        cache.set(key, True, timeout=5)
    else:
        cache.delete(key)

    return JsonResponse({'status': 'ok'})


@login_required
def api_mark_read(request, conversation_id):
    """Mark all messages in conversation as read."""
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    Message.objects.filter(
        conversation=conversation, is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    return JsonResponse({'status': 'ok'})


@login_required
def api_conversations(request):
    """Get conversation list with unread counts (for polling/refresh)."""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_msg_time', '-updated_at')

    # Check typing indicators
    from django.core.cache import cache

    data = []
    for conv in conversations:
        last_msg = conv.last_message()
        # Get who is typing
        typing_users = []
        for p in conv.participants.exclude(id=request.user.id):
            key = f"typing_{conv.id}_{p.id}"
            if cache.get(key):
                typing_users.append(p.username)

        if conv.conversation_type == 'private':
            other = conv.get_other_participant(request.user)
            display_name = other.username if other else 'Unknown'
            avatar = other.profile_picture.url if other and other.profile_picture else None
        else:
            display_name = conv.name or f"Group #{conv.id}"
            avatar = conv.group_icon.url if conv.group_icon else None

        data.append({
            'id': conv.id,
            'name': display_name,
            'type': conv.conversation_type,
            'avatar': avatar,
            'unread_count': conv.unread_count,
            'typing_users': typing_users,
            'last_message': {
                'content': last_msg.content if last_msg else '',
                'sender': last_msg.sender.username if last_msg else '',
                'time': last_msg.created_at.strftime('%I:%M %p') if last_msg else '',
                'type': last_msg.message_type if last_msg else 'text',
            } if last_msg else None,
        })

    return JsonResponse({'conversations': data})


@login_required
def api_user_list(request):
    """Get list of all users for starting conversations."""
    users = User.objects.exclude(id=request.user.id).filter(is_active=True)
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    data = []
    for u in users[:50]:
        data.append({
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name() or u.username,
            'role': u.get_role_display(),
            'profile_picture': u.profile_picture.url if u.profile_picture else None,
            'department': u.department or '',
        })

    return JsonResponse({'users': data})


# ─── Edit & Delete Messages ───────────────────────────────────────────

@login_required
@require_POST
def api_edit_message(request):
    """Edit a message (only by sender, only text messages)."""
    data = json.loads(request.body)
    message_id = data.get('message_id')
    new_content = data.get('content', '').strip()

    if not new_content:
        return JsonResponse({'status': 'error', 'message': 'Content cannot be empty'}, status=400)

    msg = get_object_or_404(Message, id=message_id, sender=request.user)

    if msg.is_deleted:
        return JsonResponse({'status': 'error', 'message': 'Message is deleted'}, status=400)

    if msg.message_type != 'text':
        return JsonResponse({'status': 'error', 'message': 'Can only edit text messages'}, status=400)

    msg.content = new_content
    msg.is_edited = True
    msg.edited_at = timezone.now()
    msg.save()

    return JsonResponse({
        'status': 'ok',
        'message': {
            'id': msg.id,
            'content': msg.content,
            'is_edited': True,
            'edited_at': msg.edited_at.strftime('%I:%M %p'),
        }
    })


@login_required
@require_POST
def api_delete_message(request):
    """Delete a message (soft delete, only by sender)."""
    data = json.loads(request.body)
    message_id = data.get('message_id')

    msg = get_object_or_404(Message, id=message_id, sender=request.user)

    msg.is_deleted = True
    msg.content = ''
    msg.file = None
    msg.save()

    return JsonResponse({'status': 'ok', 'message_id': msg.id})


# ─── Call Signaling Endpoints ─────────────────────────────────────────

@login_required
@require_POST
def api_initiate_call(request):
    """Initiate a call."""
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    call_type = data.get('call_type', 'voice')

    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )

    call = CallLog.objects.create(
        conversation=conversation,
        caller=request.user,
        call_type=call_type,
        status='ringing'
    )

    # Store call signal in cache for recipient to poll
    from django.core.cache import cache
    for participant in conversation.participants.exclude(id=request.user.id):
        key = f"incoming_call_{participant.id}"
        cache.set(key, {
            'call_id': call.id,
            'caller_id': request.user.id,
            'caller_name': request.user.username,
            'caller_avatar': request.user.profile_picture.url if request.user.profile_picture else None,
            'call_type': call_type,
            'conversation_id': conversation.id,
        }, timeout=60)

    return JsonResponse({
        'status': 'ok',
        'call_id': call.id,
    })


@login_required
@require_POST
def api_respond_call(request):
    """Accept or reject a call."""
    data = json.loads(request.body)
    call_id = data.get('call_id')
    action = data.get('action')  # 'accept' or 'reject'

    call = get_object_or_404(CallLog, id=call_id)

    from django.core.cache import cache

    if action == 'accept':
        call.status = 'accepted'
        call.save()
        cache.delete(f"incoming_call_{request.user.id}")
        cache.set(f"call_response_{call.id}", 'accepted', timeout=30)
    elif action == 'reject':
        call.status = 'rejected'
        call.save()
        cache.delete(f"incoming_call_{request.user.id}")
        cache.set(f"call_response_{call.id}", 'rejected', timeout=30)
        # Create a call message in the conversation
        _create_call_message(call)
    elif action == 'end':
        call.status = 'ended'
        call.ended_at = timezone.now()
        call.save()
        cache.set(f"call_response_{call.id}", 'ended', timeout=30)
        for participant in call.conversation.participants.all():
            cache.delete(f"incoming_call_{participant.id}")
        # Create a call message in the conversation
        _create_call_message(call)
    elif action == 'missed':
        call.status = 'missed'
        call.save()
        cache.set(f"call_response_{call.id}", 'missed', timeout=30)
        for participant in call.conversation.participants.all():
            cache.delete(f"incoming_call_{participant.id}")
        _create_call_message(call)

    return JsonResponse({'status': 'ok'})


def _create_call_message(call):
    """Create a system message for a call event in the conversation."""
    duration = ''
    if call.ended_at and call.started_at:
        diff = call.ended_at - call.started_at
        total_secs = int(diff.total_seconds())
        if total_secs >= 60:
            mins = total_secs // 60
            secs = total_secs % 60
            duration = f' ({mins}m {secs}s)'
        elif total_secs > 0:
            duration = f' ({total_secs}s)'

    call_icon = '📞' if call.call_type == 'voice' else '📹'
    if call.status == 'ended':
        content = f'{call_icon} Call ended{duration}'
    elif call.status == 'rejected':
        content = f'{call_icon} Declined call'
    elif call.status == 'missed':
        content = f'{call_icon} Missed call'
    else:
        content = f'{call_icon} Call ({call.get_status_display()})'

    Message.objects.create(
        conversation=call.conversation,
        sender=call.caller,
        content=content,
        message_type='call',
        call_log=call,
    )


@login_required
@require_POST
def api_call_signal(request):
    """Exchange WebRTC signaling data (offer/answer/ICE candidates)."""
    data = json.loads(request.body)
    call_id = data.get('call_id')
    signal_type = data.get('type')  # 'offer', 'answer', 'ice-candidate'
    signal_data = data.get('data')

    from django.core.cache import cache

    # Store signal for the other party to pick up
    key = f"call_signal_{call_id}_{request.user.id}"
    signals = cache.get(key, [])
    signals.append({'type': signal_type, 'data': signal_data})
    cache.set(key, signals, timeout=60)

    return JsonResponse({'status': 'ok'})


@login_required
def api_call_status(request, call_id):
    """Poll call status and get signaling data."""
    from django.core.cache import cache

    # Check for incoming call (works even with call_id=0)
    incoming = cache.get(f"incoming_call_{request.user.id}")

    if call_id == 0:
        return JsonResponse({
            'call_id': 0,
            'status': None,
            'response': None,
            'signals': [],
            'incoming_call': incoming,
        })

    call = get_object_or_404(CallLog, id=call_id)

    # Get response status
    response = cache.get(f"call_response_{call_id}")

    # Get signals from other participants
    signals = []
    for participant in call.conversation.participants.exclude(id=request.user.id):
        key = f"call_signal_{call_id}_{participant.id}"
        participant_signals = cache.get(key, [])
        signals.extend(participant_signals)
        if participant_signals:
            cache.delete(key)  # Clear after reading

    return JsonResponse({
        'call_id': call_id,
        'status': call.status,
        'response': response,
        'signals': signals,
        'incoming_call': incoming,
    })
