from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """A conversation can be one-to-one or a group chat."""
    CONVERSATION_TYPES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]

    name = models.CharField(max_length=200, blank=True, null=True)
    conversation_type = models.CharField(max_length=10, choices=CONVERSATION_TYPES, default='private')
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations', blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_conversations'
    )
    group_icon = models.ImageField(upload_to='group_icons/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.conversation_type == 'group':
            return self.name or f"Group #{self.pk}"
        participants = self.participants.all()[:2]
        return " & ".join([p.username for p in participants])

    def get_other_participant(self, user):
        """For private chats, get the other user."""
        return self.participants.exclude(id=user.id).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """A message in a conversation."""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('voice', 'Voice'),
        ('call', 'Call'),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField(blank=True, default='')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file = models.FileField(upload_to='chat_files/%Y/%m/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    call_log = models.ForeignKey(
        'CallLog', on_delete=models.SET_NULL, null=True, blank=True, related_name='message'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class CallLog(models.Model):
    """Log of voice/video calls."""
    CALL_TYPES = [
        ('voice', 'Voice'),
        ('video', 'Video'),
    ]
    CALL_STATUS = [
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('missed', 'Missed'),
        ('ended', 'Ended'),
    ]

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='calls'
    )
    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='outgoing_calls'
    )
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='ringing')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.caller.username} - {self.call_type} ({self.status})"
