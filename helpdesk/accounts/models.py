from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access control."""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager_it', 'Manager IT'),
        ('it_staff', 'IT Staff'),
        ('agent', 'Agent'),
        ('user', 'User'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager_it(self):
        return self.role == 'manager_it'

    @property
    def is_it_staff(self):
        return self.role == 'it_staff'

    @property
    def is_agent(self):
        return self.role == 'agent'

    @property
    def is_regular_user(self):
        return self.role == 'user'

    @property
    def can_manage_tickets(self):
        """Admin, Manager IT, IT Staff, Agent can all manage tickets."""
        return self.role in ('admin', 'manager_it', 'it_staff', 'agent')
