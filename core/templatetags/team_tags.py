# templatetags/team_tags.py
from django import template
from teams.models import TeamCaptain

register = template.Library()

@register.filter
def teamcaptain_email_exists(email):
    return TeamCaptain.objects.filter(email=email, user__isnull=True).exists()