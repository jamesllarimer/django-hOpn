from django.db import models
from accounts.models import CustomUser
from players.models import FreeAgent
from teams.models import Team

class TeamInvitation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('EXPIRED', 'Expired')
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='sent_invitations')
    free_agent = models.ForeignKey(FreeAgent, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    response_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)  # Optional message from team captain

    class Meta:
        unique_together = ['team', 'free_agent']  # Prevent duplicate invitations

class TeamInvitationNotification(models.Model):
    """
    Represents a notification for team invitations
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='team_notifications')
    invitation = models.ForeignKey(TeamInvitation, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation notification for {self.user.username} - {self.invitation}"