import random
import string
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from accounts.models import CustomUser
from leagues.models import League, Division

def generate_unique_signup_code():
    """Generate a unique signup code for teams"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Team.objects.filter(signup_code=code).exists():
            return code

class TeamCaptain(models.Model):
    """
    Represents a team captain who may not have a user account
    Can be linked to a full user account if/when they register
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='team_captains'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_captain = models.BooleanField(default=False)  # Flag for system-generated captain

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
        
    @classmethod
    def get_default_captain(cls):
        system_captain, _ = cls.objects.get_or_create(
            is_system_captain=True,
            defaults={
                'first_name': 'System',
                'last_name': 'Admin',
                'email': 'admin@example.com',
                'phone_number': '000-000-0000'
            }
        )
        return system_captain.id

class Team(models.Model):
    """
    Represents a team within a league and division
    """
    name = models.CharField(max_length=200)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='teams')
    captain = models.ForeignKey(
        TeamCaptain, 
        on_delete=models.PROTECT,
        related_name='captained_teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    signup_code = models.CharField(max_length=8, unique=True, null=True, blank=True)
    
    def get_signup_url(self):
        """Generate the signup URL for this team"""
        return reverse('teams:team_signup', kwargs={'signup_code': self.signup_code})
        
    def save(self, *args, **kwargs):
        if not self.signup_code:
            self.signup_code = generate_unique_signup_code()
        super().save(*args, **kwargs)

    def clean(self):
        if self.division and self.league:
            if self.division.sport != self.league.sport:
                raise ValidationError("Division must belong to the same sport as the league")
    
    def __str__(self):
        return f"{self.name} - {self.league.name} - {self.division.name}"