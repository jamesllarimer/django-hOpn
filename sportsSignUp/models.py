import json
import random
import string
from django.db.models import Q
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.urls import reverse
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
        return (
            TeamCaptain.objects.filter(
            Q(user=self) |  # User is directly linked as captain
            Q(email=self.email, user__isnull=True)  # Email matches an unlinked captain
            ).exists()
    )

class TeamCaptain(models.Model):
    """
    Represents a team captain who may not have a user account
    Can be linked to a full user account if/when they register
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    user = models.ForeignKey(CustomUser, 
                            on_delete=models.SET_NULL, 
                            null=True, 
                            blank=True,
                            related_name='team_captains')
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
    @property
    def has_registration_form(self):
        return hasattr(self, 'registration_form') and self.registration_form.is_active
    
    # Stripe integration
    stripe_product = models.ForeignKey(
        'StripeProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leagues',
        help_text="Stripe product associated with this league"
    )
    
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
        if self.registration_start_date and self.registration_end_date:
            if self.registration_start_date > self.registration_end_date:
                raise ValidationError("Registration start date must be before end date")
        
        if self.registration_end_date and self.league_start_date:
            if self.registration_end_date > self.league_start_date:
                raise ValidationError("Registration end date must be before league start date")
        
        if self.league_start_date and self.league_end_date:
            if self.league_start_date > self.league_end_date:
                raise ValidationError("League start date must be before end date")
    
    def __str__(self):
        return f"{self.name} - {self.sport.name}"

    def get_stripe_price_id(self, is_member=False, is_early_registration=False):
        """
        Get the appropriate Stripe price ID based on membership status and registration timing
        """
        if not self.stripe_product:
            return None

        prices = self.stripe_product.prices.filter(active=True)
        
        # Filter based on metadata
        for price in prices.all():
            metadata = price.metadata
            if (metadata.get('is_member', '').lower() == str(is_member).lower() and 
                metadata.get('is_early_registration', '').lower() == str(is_early_registration).lower()):
                return price.stripe_id
                
        return None

def generate_unique_signup_code():
    """Generate a unique signup code for teams"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Team.objects.filter(signup_code=code).exists():
            return code

class Team(models.Model):
    """
    Represents a team within a league and division
    """
    name = models.CharField(max_length=200)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='teams')
    captain = models.ForeignKey(TeamCaptain, 
                               on_delete=models.PROTECT,
                               related_name='captained_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    signup_code = models.CharField(max_length=8, unique=True, null=True, blank=True)  # Make it nullable initially
    
    def get_signup_url(self):
        """Generate the signup URL for this team"""
        from django.urls import reverse
        return reverse('sportsSignUp:team_signup', kwargs={'signup_code': self.signup_code})
        
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
    3
    # Optional link to user account
    user = models.ForeignKey(CustomUser, 
                            on_delete=models.SET_NULL, 
                            null=True, 
                            blank=True,
                            related_name='linked_players')
    
    # Make team optional for free agents
    team = models.ForeignKey(Team, 
                            on_delete=models.CASCADE, 
                            related_name='players',
                            null=True,  # Allow null for free agents
                            blank=True)  # Make it optional in forms
    
    is_active = models.BooleanField(default=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        if self.team:
            return f"{self.get_full_name()} - {self.team.name}"
        return f"{self.get_full_name()} (Free Agent)"

class Registration(models.Model):
    """
    Tracks player registrations for leagues
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='registrations')
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='registrations')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    
    # Payment information
    payment_status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ], default='pending')
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    stripe_checkout_session = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    is_late_registration = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('player', 'league')  # Prevent duplicate registrations
    
    def __str__(self):
        return f"{self.player.get_full_name()} - {self.league.name} ({self.payment_status})"

class StripeProduct(models.Model):
    stripe_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class StripePrice(models.Model):
    RECURRING_INTERVAL_CHOICES = [
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
    ]

    stripe_id = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(StripeProduct, on_delete=models.CASCADE, related_name='prices')
    currency = models.CharField(max_length=3)  # ISO currency code
    unit_amount = models.IntegerField()  # Amount in cents
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True)  
    # Recurring fields (null if one-time price)
    recurring = models.BooleanField(default=False)
    recurring_interval = models.CharField(
        max_length=5,
        choices=RECURRING_INTERVAL_CHOICES,
        null=True,
        blank=True
    )
    recurring_interval_count = models.IntegerField(null=True, blank=True)
    
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        amount = self.unit_amount / 100  # Convert cents to currency units
        if self.recurring:
            return f"{self.currency} {amount} / {self.recurring_interval}"
        return f"{self.currency} {amount} (one-time)"
    

class FreeAgent(models.Model):
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


class TeamInvitation(models.Model):
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

class TeamInvitationNotification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='team_notifications')
    invitation = models.ForeignKey(TeamInvitation, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class DynamicForm(models.Model):
    """Model to store form configurations for league registrations"""
    league = models.OneToOneField('League', on_delete=models.CASCADE, related_name='registration_form')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Registration Form - {self.league.name}"

class FormField(models.Model):
    """Model to store individual form fields"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number Input'),
        ('email', 'Email Input'),
        ('date', 'Date Input'),
        ('checkbox', 'Checkbox'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('file', 'File Upload'),
    ]

    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    options = models.JSONField(null=True, blank=True, 
        help_text="For select/radio fields, provide options as JSON array")
    validation_rules = models.JSONField(null=True, blank=True,
        help_text="JSON object with validation rules")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def clean(self):
        if self.field_type in ['select', 'radio'] and not self.options:
            raise ValidationError('Options are required for select and radio fields')
        
        if self.options:
            try:
                if not isinstance(json.loads(self.options), list):
                    raise ValidationError('Options must be a JSON array')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format for options')

    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"

class FormResponse(models.Model):
    """Model to store user responses to dynamic forms"""
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='form_responses')
    registration = models.OneToOneField('Registration', on_delete=models.CASCADE, related_name='form_response')
    responses = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response for {self.form} by {self.user}"