from django.db import models
from django.core.exceptions import ValidationError

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
    available_divisions = models.ManyToManyField(
        Division, 
        related_name='league_sessions', 
        limit_choices_to={'sport': models.F('sport')}
    )
    
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