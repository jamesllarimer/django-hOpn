from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class CustomUser(AbstractUser):
    """
    Extended user model to distinguish between admin users and customers
    """
    USER_TYPES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    
    # Additional profile information
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Add unique related_name to avoid conflicts with default User model
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
        """Check if the user is an admin"""
        return self.user_type == 'admin'

class Sport(models.Model):
    """
    Represents different sports offered by the organization
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Division(models.Model):
    """
    Represents divisions within a sport
    Divisions are sport-specific and can be used across multiple leagues
    """
    name = models.CharField(max_length=100)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='divisions')
    
    # Additional division-specific details
    skill_level = models.CharField(max_length=50, blank=True)
    age_group = models.CharField(max_length=50, blank=True)
    
    class Meta:
        unique_together = ('name', 'sport')
    
    def __str__(self):
        return f"{self.name} - {self.sport.name}"

class League(models.Model):
    """
    Represents a specific league for a sport
    """
    name = models.CharField(max_length=200)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='leagues')
    
    # Available divisions for this league session
    available_divisions = models.ManyToManyField(Division, 
                                                 related_name='league_sessions', 
                                                 limit_choices_to={'sport': models.F('sport')})
    
    # Stripe integration
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Registration details
    registration_start_date = models.DateField()
    registration_end_date = models.DateField()
    early_registration_deadline = models.DateField()
    league_start_date = models.DateField()
    league_end_date = models.DateField()
    
    # Pricing
    regular_registration_price = models.DecimalField(max_digits=10, decimal_places=2)
    early_registration_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional details
    description = models.TextField(blank=True)
    max_teams = models.IntegerField(null=True, blank=True)
    
    def clean(self):
        """
        Validate date relationships and ensure divisions are from the same sport
        """
        # Date validations
        if self.registration_start_date and self.registration_end_date:
            if self.registration_start_date > self.registration_end_date:
                raise ValidationError("Registration start date must be before end date")
        
        if self.registration_end_date and self.league_start_date:
            if self.registration_end_date > self.league_start_date:
                raise ValidationError("Registration end date must be before league start date")
        
        if self.league_start_date and self.league_end_date:
            if self.league_start_date > self.league_end_date:
                raise ValidationError("League start date must be before end date")
    
    def is_registration_open(self):
        """
        Check if registration is currently open
        """
        now = timezone.now().date()
        return (self.registration_start_date <= now <= self.registration_end_date)
    
    def is_early_registration_active(self):
        """
        Check if early registration is currently active
        """
        now = timezone.now().date()
        return (self.registration_start_date <= now <= self.early_registration_deadline)
    
    def __str__(self):
        return f"{self.name} - {self.sport.name}"

class Team(models.Model):
    """
    Represents a team within a league and division
    """
    name = models.CharField(max_length=200)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='teams')
    
    # Team captains (multiple allowed)
    captains = models.ManyToManyField(CustomUser, 
                                      related_name='captained_teams', 
                                      blank=True)
    
    # Team details
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        """
        Validate that the division belongs to the league's sport
        """
        if self.division and self.league:
            if self.division.sport != self.league.sport:
                raise ValidationError("Division must belong to the same sport as the league")
    
    def __str__(self):
        return f"{self.name} - {self.league.name} - {self.division.name}"

class Player(models.Model):
    """
    Represents a player's participation in teams
    Allows multiple team memberships
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='players')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    
    # Player-specific details
    jersey_number = models.CharField(max_length=10, blank=True)
    position = models.CharField(max_length=50, blank=True)
    
    # Additional tracking
    joined_team_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        # Prevent duplicate team memberships in the same league
        unique_together = ('user', 'team')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team.name}"

class Registration(models.Model):
    """
    Tracks player registrations for leagues
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='registrations')
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='registrations')
    
    # Registration details
    registered_at = models.DateTimeField(auto_now_add=True)
    is_early_registration = models.BooleanField(default=False)
    registration_type = models.CharField(max_length=50, choices=[
        ('individual', 'Individual'),
        ('team', 'Team'),
    ])
    
    # Payment tracking
    payment_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        unique_together = ('player', 'league')
    
    def save(self, *args, **kwargs):
        """
        Automatically set early registration flag
        """
        if not self.pk:  # Only on creation
            league = self.league
            now = timezone.now().date()
            self.is_early_registration = (league.registration_start_date <= now <= league.early_registration_deadline)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.player.user.get_full_name()} - {self.league.name}"