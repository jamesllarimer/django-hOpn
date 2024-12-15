from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q

class CustomUser(AbstractUser):
    """
    Extended user model to distinguish between admin users and customers
    """
    USER_TYPES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Add unique related_name to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    def is_admin(self):
        return self.user_type == 'admin'

    def is_team_captain(self):
        """
        Check if user is a team captain.
        Note: This will need to be updated once TeamCaptain model is moved to teams app
        """
        from teams.models import TeamCaptain  # Avoid circular import
        return (
            TeamCaptain.objects.filter(
                Q(user=self) |  # User is directly linked as captain
                Q(email=self.email, user__isnull=True)  # Email matches an unlinked captain
            ).exists()
        )