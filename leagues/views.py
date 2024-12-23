from venv import logger
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView
from django.db.models import Prefetch
from .models import League, Sport
from django.template.loader import get_template

class LeagueListView(ListView):
    template_name = 'leagues/league_list.html'
    context_object_name = 'sports'
    
    def get_queryset(self):
        # Debug prints
        print(f"Checking template directories:")
        for template_setting in settings.TEMPLATES:
            print(f"Template dirs: {template_setting['DIRS']}")
        
        try:
            # Try to explicitly load base.html
            template = get_template('base.html')
            print(f"Found base.html at: {template.origin.name}")
        except Exception as e:
            print(f"Error loading base.html: {e}")
        
        today = timezone.now().date()
        active_leagues = League.objects.filter(
            registration_start_date__lte=today,
            registration_end_date__gte=today
        ).select_related('sport').prefetch_related('available_divisions')
        
        return Sport.objects.prefetch_related(
            Prefetch('leagues', queryset=active_leagues, to_attr='active_leagues')
        ).all()

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