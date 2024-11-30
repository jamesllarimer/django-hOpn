from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from .models import Sport, Team, Player, Division, League


def index(request):
    teams_list = Team.objects.all()
    context = {
        "teams": teams_list,
    }
    return render(request, "index.html", context)

def active_leagues(request):
    """
    View to display currently active leagues
    A league is considered active if:
    1. Registration has started
    2. Registration has not ended
    """
    # Get current date
    today = timezone.now().date()

    # Filter for active leagues
    active_leagues = League.objects.filter(
        registration_start_date__lte=today,  # Registration has started
        registration_end_date__gte=today     # Registration has not ended
    ).order_by('registration_end_date')

    context = {
        'active_leagues': active_leagues,
        'page_title': 'Active Leagues'
    }

    return render(request, 'active_leagues.html', context)