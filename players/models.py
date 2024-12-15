from django.db import models
from accounts.models import CustomUser
from teams.models import Team
from leagues.models import League, Division

class Player(models.Model):
    """
    Represents a player who may or may not have a team yet
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    parent_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField()
    membership_number = models.CharField(max_length=50, null=True, blank=True)
    is_member = models.BooleanField(default=False)
    
    # Optional link to user account
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='linked_players'
    )
    
    # Make team optional for free agents
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='players',
        null=True,  # Allow null for free agents
        blank=True
    )
    
    is_active = models.BooleanField(default=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        if self.team:
            return f"{self.get_full_name()} - {self.team.name}"
        return f"{self.get_full_name()} (Free Agent)"

class FreeAgent(models.Model):
    """
    Represents a player looking to join a team
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='free_agent_profiles')
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='free_agents')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='free_agents')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    membership_number = models.CharField(max_length=100)
    is_member = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('AVAILABLE', 'Available'),
            ('INVITED', 'Invited'),
            ('JOINED', 'Joined'),
            ('INACTIVE', 'Inactive')
        ],
        default='AVAILABLE'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.league.name}"

    class Meta:
        unique_together = ['user', 'league']  # One free agent profile per league per user