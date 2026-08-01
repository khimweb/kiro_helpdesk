from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SLA(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, unique=True)
    response_time_hours = models.PositiveIntegerField(default=24)
    resolution_time_hours = models.PositiveIntegerField(default=72)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'SLA - {self.get_priority_display()}'


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='tickets')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.ticket_id}] {self.title}'


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text='Internal notes are only visible to agents/admins')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on {self.ticket.ticket_id}'


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

    @property
    def raw_url(self):
        """Return correct URL - fixes Cloudinary image/upload → raw/upload for non-image files."""
        url = self.file.url
        ext = self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico'}
        if ext not in image_exts:
            url = url.replace('/image/upload/', '/raw/upload/')
        return url

    def __str__(self):
        return f'Attachment for {self.ticket.ticket_id}'


class CommentAttachment(models.Model):
    comment = models.ForeignKey(TicketComment, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='comment_attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

    @property
    def raw_url(self):
        """Return correct URL - fixes Cloudinary image/upload → raw/upload for non-image files."""
        url = self.file.url
        ext = self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico'}
        if ext not in image_exts:
            # Cloudinary serves non-images correctly only via /raw/upload/
            url = url.replace('/image/upload/', '/raw/upload/')
        return url

    @property
    def file_icon(self):
        ext = self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
        icons = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word', 'docx': 'fa-file-word',
            'xls': 'fa-file-excel', 'xlsx': 'fa-file-excel',
            'jpg': 'fa-file-image', 'jpeg': 'fa-file-image',
            'png': 'fa-file-image', 'gif': 'fa-file-image',
            'zip': 'fa-file-archive', 'rar': 'fa-file-archive',
            'txt': 'fa-file-alt',
            'exe': 'fa-file-code',
        }
        return icons.get(ext, 'fa-file')

    def __str__(self):
        return f'Attachment for comment {self.comment.id}'


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} on {self.ticket.ticket_id} by {self.user.username}'


class TicketAssignment(models.Model):
    """Tracks the full assignment workflow: Admin → Manager IT → IT Staff."""

    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='assignment')

    # Admin check
    admin_checked = models.BooleanField(default=False)
    admin_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='admin_checks'
    )
    admin_checked_at = models.DateTimeField(null=True, blank=True)

    # Assigned to Manager IT
    assigned_to_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='manager_assignments'
    )
    assigned_to_manager_at = models.DateTimeField(null=True, blank=True)

    # Manager IT check
    manager_checked = models.BooleanField(default=False)
    manager_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='manager_checks'
    )
    manager_checked_at = models.DateTimeField(null=True, blank=True)

    # Assigned to IT Staff
    assigned_to_it_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='it_staff_assignments'
    )
    assigned_to_it_staff_at = models.DateTimeField(null=True, blank=True)

    # IT Staff completed
    it_staff_completed = models.BooleanField(default=False)
    it_staff_completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='it_staff_completions'
    )
    it_staff_completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Assignment for {self.ticket.ticket_id}'

    @property
    def current_stage(self):
        if self.it_staff_completed:
            return 'completed'
        if self.assigned_to_it_staff:
            return 'it_staff'
        if self.manager_checked:
            return 'manager_checked'
        if self.assigned_to_manager:
            return 'manager'
        if self.admin_checked:
            return 'admin_checked'
        return 'pending'


class AIChatSession(models.Model):
    """A multi-turn AI chat conversation for one user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_sessions'
    )
    title = models.CharField(max_length=200, blank=True, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} ({self.user.username})'

    def auto_title_from_message(self, message: str, max_len: int = 60):
        text = (message or '').strip().replace('\n', ' ')
        if not text:
            return
        self.title = text[:max_len] + ('…' if len(text) > max_len else '')
        self.save(update_fields=['title', 'updated_at'])


class AIChatMessage(models.Model):
    """Single message in an AI chat session."""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(
        AIChatSession, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
