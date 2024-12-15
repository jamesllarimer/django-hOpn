from venv import logger
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView

from api.client import ApiClient
from .models import Sport, League

def active_leagues(request):
    """
    View to display currently active leagues
    A league is considered active if:
    1. Registration has started
    2. Registration has not ended
    """
    today = timezone.now().date()

    active_leagues = League.objects.filter(
        registration_start_date__lte=today,  # Registration has started
        registration_end_date__gte=today     # Registration has not ended
    ).order_by('registration_end_date')

    context = {
        'active_leagues': active_leagues,
        'page_title': 'Active Leagues'
    }

    return render(request, 'leagues/active_leagues.html', context)

class LeagueListView(ListView):
    template_name = 'leagues/league_list.html'
    context_object_name = 'sports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = ApiClient(self.request)
        
        try:
            # Get sports with active leagues from API
            sports_data = api_client.get('sports/active-leagues/')
            context['sports'] = sports_data
            
        except Exception as e:
            logger.error(f"API call failed in LeagueListView: {str(e)}")
            # Fallback to direct database query
            today = timezone.now().date()
            sports = Sport.objects.prefetch_related('leagues').all()
            
            # Filter for active leagues
            for sport in sports:
                sport.active_leagues = sport.leagues.filter(
                    registration_start_date__lte=today,
                    registration_end_date__gte=today
                ).select_related('sport').prefetch_related('available_divisions')
            
            context['sports'] = sports
            
        return context

def active_leagues(request):
    """
    View to display currently active leagues
    """
    api_client = ApiClient(request)
    
    try:
        # Get active leagues from API
        active_leagues = api_client.get('leagues/active/')
        context = {
            'active_leagues': active_leagues,
            'page_title': 'Active Leagues'
        }
        
    except Exception as e:
        logger.error(f"API call failed in active_leagues: {str(e)}")
        # Fallback to direct database query
        today = timezone.now().date()
        active_leagues = League.objects.filter(
            registration_start_date__lte=today,
            registration_end_date__gte=today
        ).order_by('registration_end_date')
        
        context = {
            'active_leagues': active_leagues,
            'page_title': 'Active Leagues'
        }

    return render(request, 'leagues/active_leagues.html', context)
def get_divisions_by_league(request, league_id):
    """Get all divisions available for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all().order_by('name')
    
    # Convert to list of dictionaries for JSON response
    divisions_data = [
        {
            'id': division.id,
            'name': division.name,
            'skill_level': division.skill_level,
            'age_group': division.age_group
        }
        for division in divisions
    ]
    
    return JsonResponse(divisions_data, safe=False)

def divisions_and_teams_by_league(request, league_id):
    """Get divisions and their teams for a league"""
    league = get_object_or_404(League, id=league_id)
    divisions = league.available_divisions.all()

    data = []
    for division in divisions:
        teams = division.teams.filter(league=league).values('id', 'name')
        data.append({
            'id': division.id,
            'name': division.name,
            'teams': list(teams)
        })

    return JsonResponse(data, safe=False)