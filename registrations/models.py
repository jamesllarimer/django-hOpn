from django.db import models
from players.models import Player
from leagues.models import League, Division

class Registration(models.Model):
    """
    Tracks player registrations for leagues
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='registrations')
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='registrations')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    
    # Payment information
    payment_status = models.CharField(
        max_length=50, 
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
            ('refunded', 'Refunded')
        ], 
        default='pending'
    )
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