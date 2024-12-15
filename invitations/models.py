from django.db import models
from accounts.models import CustomUser
from teams.models import Team
from players.models import FreeAgent

class TeamInvitation(models.Model):
    """
    Represents an invitation from a team to a free agent
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='sent_invitations')
    free_agent = models.ForeignKey(FreeAgent, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('DECLINED', 'Declined'),
            ('EXPIRED', 'Expired')
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    response_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)  # Optional message from team captain

    class Meta:
        unique_together = ['team', 'free_agent']  # Prevent duplicate invitations

    def __str__(self):
        return f"{self.team.name} → {self.free_agent.get_full_name()} ({self.status})"

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